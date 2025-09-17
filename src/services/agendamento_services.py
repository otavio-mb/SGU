# Service para gerenciamento de agendamentos
# Contém toda a lógica de negócio relacionada aos agendamentos

# bibliotecas
from datetime import datetime, timedelta, time
from typing import List, Dict
from models.agendamento_model import AgendamentoModel
from models.servicos_model import ServicoModel
from models.profissional_model import ProfissionalModel


class AgendamentoService:
    
    # Service responsável pela lógica de negócio dos agendamentos
    
    # Horários de funcionamento e intervalo de almoço
    HORA_ABERTURA = 9  # abre às 9h
    HORA_FECHAMENTO = 20  # fecha às 20h
    HORA_ALMOCO_INICIO = 12  # almoço começa às 12h
    HORA_ALMOCO_FIM = 13  # almoço termina às 13h
    
    # Duração padrão de cada tipo de serviço (em minutos)
    DURACAO_SERVICOS = {
        'alisamento': 30,
        'corte tesoura': 60,
        'corte maquina': 60,
        'barba': 30,
        'sobrancelha': 10,
        'pintura': 120
    }
    
    @staticmethod
    def criar_agendamento(dt_atendimento: datetime, id_user: int, 
                         id_profissional: int, servicos_ids: List[int],
                         observacoes: str = None) -> Dict:
        
        # Cria agendamento(s) para os serviços solicitados em uma data e hora específicas.
        
        try:
            # Valida dados básicos (tipos e valores)
            if not AgendamentoService._validar_dados_basicos(
                dt_atendimento, id_user, id_profissional, servicos_ids):
                return {"erro": "Dados inválidos fornecidos"}
            
            # Não permite agendar para data/hora passadas
            if dt_atendimento <= datetime.utcnow():
                return {"erro": "Não é possível agendar para datas passadas"}
            
            # Verifica se horário está dentro do funcionamento
            if not AgendamentoService._verificar_horario_funcionamento(dt_atendimento):
                return {"erro": "Horário fora do funcionamento do estabelecimento"}
            
            # Busca os serviços e calcula duração e valor total
            servicos = []
            duracao_total = 0
            valor_total = 0
            
            for servico_id in servicos_ids:
                servico = ServicoModel.find_by_id(servico_id)
                if not servico:
                    return {"erro": f"Serviço com ID {servico_id} não encontrado"}
                
                servicos.append(servico)
                duracao_total += AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)  # padrão 60 min se não achar
                valor_total += float(servico.preco)
            
            # Verifica se o profissional está disponível no período total
            dt_fim = dt_atendimento + timedelta(minutes=duracao_total)
            if not AgendamentoService._verificar_disponibilidade(
                id_profissional, dt_atendimento, dt_fim):
                return {"erro": "Horário não disponível para o profissional"}
            
            # Cria um agendamento para cada serviço, sequencialmente
            agendamentos_criados = []
            dt_atual = dt_atendimento
            
            for i, servico in enumerate(servicos):
                duracao_servico = AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)
                
                agendamento = AgendamentoModel(
                    dt_atendimento=dt_atual,
                    id_user=id_user,
                    id_profissional=id_profissional,
                    id_servico=servico.id,
                    observacoes=observacoes if i == 0 else None,  # só no primeiro serviço
                    valor_total=float(servico.preco)
                )
                
                agendamento.save()
                agendamentos_criados.append(agendamento)
                
                # Atualiza hora para próximo serviço
                dt_atual += timedelta(minutes=duracao_servico)
            
            # Retorna dados do agendamento criado
            return {
                "sucesso": True,
                "agendamentos": [ag.to_dict() for ag in agendamentos_criados],
                "valor_total": valor_total,
                "duracao_total": duracao_total
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def cancelar_agendamento(agendamento_id: int, user_id: int) -> Dict:
        
        # Cancela um agendamento, verificando permissões e status.
        
        try:
            agendamento = AgendamentoModel.find_by_id(agendamento_id)
            
            # Verifica se agendamento existe
            if not agendamento:
                return {"erro": "Agendamento não encontrado"}
            
            # Verifica se o usuário é dono do agendamento
            if agendamento.id_user != user_id:
                return {"erro": "Acesso negado: agendamento não pertence ao usuário"}
            
            # Verifica se já foi cancelado ou finalizado
            if agendamento.status == 'cancelado':
                return {"erro": "Agendamento já foi cancelado"}
            
            if agendamento.status == 'finalizado':
                return {"erro": "Não é possível cancelar um agendamento finalizado"}
            
            # Calcula taxa de cancelamento se aplicável
            servico = ServicoModel.find_by_id(agendamento.id_servico)
            taxa = 0.0
            
            if not agendamento.pode_cancelar_gratuito():
                taxa = agendamento.calcular_taxa_cancelamento(float(servico.preco))
            
            # Atualiza status e taxa no agendamento
            agendamento.update(
                status='cancelado',
                taxa_cancelamento=taxa
            )
            
            return {
                "sucesso": True,
                "agendamento": agendamento.to_dict(),
                "taxa_cancelamento": taxa,
                "cancelamento_gratuito": taxa == 0
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def listar_horarios_disponiveis(profissional_id: int, data: datetime.date) -> Dict:
        
        # Lista os horários disponíveis para um profissional em um determinado dia.
        
        try:
            # Verifica se profissional existe
            if not ProfissionalModel.find_by_id(profissional_id):
                return {"erro": "Profissional não encontrado"}
            
            # Busca agendamentos do profissional na data
            agendamentos = AgendamentoModel.find_by_profissional_data(profissional_id, data)
            
            # Marca horários já ocupados em slots de 30 minutos
            horarios_disponiveis = []
            horarios_ocupados = set()
            
            for agendamento in agendamentos:
                servico = ServicoModel.find_by_id(agendamento.id_servico)
                duracao = AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)
                
                inicio = agendamento.dt_atendimento
                fim = inicio + timedelta(minutes=duracao)
                
                # Marca todos os intervalos de 30 min como ocupados
                slot_atual = inicio
                while slot_atual < fim:
                    horarios_ocupados.add(slot_atual.strftime("%H:%M"))
                    slot_atual += timedelta(minutes=30)
            
            # Gera horários dentro do horário comercial, pulando almoço
            data_completa = datetime.combine(data, time(AgendamentoService.HORA_ABERTURA))
            
            while data_completa.hour < AgendamentoService.HORA_FECHAMENTO:
                # Pula horário de almoço
                if (data_completa.hour >= AgendamentoService.HORA_ALMOCO_INICIO and 
                    data_completa.hour < AgendamentoService.HORA_ALMOCO_FIM):
                    data_completa += timedelta(minutes=30)
                    continue
                
                horario_str = data_completa.strftime("%H:%M")
                
                # Se não ocupado, adiciona como disponível
                if horario_str not in horarios_ocupados:
                    horarios_disponiveis.append({
                        "horario": horario_str,
                        "timestamp": data_completa.isoformat()
                    })
                
                data_completa += timedelta(minutes=30)
            
            return {
                "sucesso": True,
                "data": data.isoformat(),
                "horarios_disponiveis": horarios_disponiveis
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def listar_agendamentos_usuario(user_id: int, 
                                   status: str = None,
                                   data_inicio: datetime = None,
                                   data_fim: datetime = None) -> Dict:
        
        # Lista agendamentos de um usuário, com filtros opcionais.
        
        try:
            agendamentos = AgendamentoModel.find_by_user(user_id)
            
            # Filtra por status, se informado
            if status:
                agendamentos = [ag for ag in agendamentos if ag.status == status]
            
            # Filtra por data inicial, se informado
            if data_inicio:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento >= data_inicio]
            
            # Filtra por data final, se informado
            if data_fim:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento <= data_fim]
            
            # Enriquecer dados com informações do serviço e profissional
            agendamentos_detalhados = []
            for agendamento in agendamentos:
                ag_dict = agendamento.to_dict()
                
                servico = ServicoModel.find_by_id(agendamento.id_servico)
                ag_dict['servico'] = {
                    'nome': servico.nome,
                    'preco': float(servico.preco),
                    'duracao': AgendamentoService.DURACAO_SERVICOS.get(
                        servico.nome.lower(), 60)
                }
                
                profissional = ProfissionalModel.find_by_id(agendamento.id_profissional)
                ag_dict['profissional'] = {
                    'nome': profissional.nome,
                    'especialidade': profissional.especialidade
                }
                
                agendamentos_detalhados.append(ag_dict)
            
            return {
                "sucesso": True,
                "agendamentos": agendamentos_detalhados
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def _validar_dados_basicos(dt_atendimento: datetime, id_user: int,
                              id_profissional: int, servicos_ids: List[int]) -> bool:
        
        # Verifica se os dados básicos estão corretos (tipos e presença).
        
        if not isinstance(dt_atendimento, datetime):
            return False
        
        if not isinstance(id_user, int) or id_user <= 0:
            return False
        
        if not isinstance(id_profissional, int) or id_profissional <= 0:
            return False
        
        if not servicos_ids or not isinstance(servicos_ids, list):
            return False
        
        return True
    
    @staticmethod
    def _verificar_horario_funcionamento(dt_atendimento: datetime) -> bool:
        
        # Verifica se o horário está dentro do expediente e não no almoço.
        
        hora = dt_atendimento.hour
        
        if hora < AgendamentoService.HORA_ABERTURA or hora >= AgendamentoService.HORA_FECHAMENTO:
            return False
        
        if (hora >= AgendamentoService.HORA_ALMOCO_INICIO and 
            hora < AgendamentoService.HORA_ALMOCO_FIM):
            return False
        
        return True
    
    @staticmethod
    def _verificar_disponibilidade(profissional_id: int, dt_inicio: datetime,
                                  dt_fim: datetime) -> bool:
        
        # Checa se o profissional está disponível no intervalo pedido.
        
        agendamentos_conflito = AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.status != 'cancelado',
            AgendamentoModel.dt_atendimento < dt_fim
        ).all()
        
        for agendamento in agendamentos_conflito:
            servico = ServicoModel.find_by_id(agendamento.id_servico)
            duracao = AgendamentoService.DURACAO_SERVICOS.get(
                servico.nome.lower(), 60)
            ag_fim = agendamento.dt_atendimento + timedelta(minutes=duracao)
            
            # Se horários se sobrepõem, retorna indisponível
            if not (dt_fim <= agendamento.dt_atendimento or dt_inicio >= ag_fim):
                return False
        
        return True