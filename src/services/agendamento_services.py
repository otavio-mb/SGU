# Service para gerenciamento de agendamentos
# Contém toda a lógica de negócio relacionada aos agendamentos

from datetime import datetime, timedelta, time
from typing import List, Dict
from ..models.agendamento_model import AgendamentoModel
from ..models.servicos_model import ServicoModel
from ..models.profissional_model import ProfissionalModel
from ..models.usuario_model import UsuarioModel
from src import db


class AgendamentoService:
    """Service responsável pela lógica de negócio dos agendamentos"""
    
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
        """Cria agendamento(s) para os serviços solicitados"""
        
        try:
            # Valida dados básicos
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
                servico = ServicoModel.query.get(servico_id)
                if not servico:
                    return {"erro": f"Serviço com ID {servico_id} não encontrado"}
                
                servicos.append(servico)
                duracao_servico = servico.horario_duracao if servico.horario_duracao else 60
                duracao_total += duracao_servico
                valor_total += float(servico.valor)
            
            # Verifica se o profissional está disponível
            dt_fim = dt_atendimento + timedelta(minutes=duracao_total)
            if not AgendamentoService._verificar_disponibilidade(
                id_profissional, dt_atendimento, dt_fim):
                return {"erro": "Horário não disponível para o profissional"}
            
            # Cria um agendamento para cada serviço
            agendamentos_criados = []
            dt_atual = dt_atendimento
            
            for i, servico in enumerate(servicos):
                duracao_servico = servico.horario_duracao if servico.horario_duracao else 60
                
                agendamento = AgendamentoModel()
                agendamento.dt_atendimento = dt_atual
                agendamento.id_user = id_user
                agendamento.id_profissional = id_profissional
                agendamento.id_servico = servico.id
                agendamento.observacoes = observacoes if i == 0 else None
                agendamento.valor_total = float(servico.valor)
                
                agendamento.salvar()
                agendamentos_criados.append(agendamento)
                
                dt_atual += timedelta(minutes=duracao_servico)
            
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
        """Cancela um agendamento"""
        
        try:
            agendamento = AgendamentoModel.find_by_id(agendamento_id)
            
            if not agendamento:
                return {"erro": "Agendamento não encontrado"}
            
            if agendamento.id_user != user_id:
                return {"erro": "Acesso negado: agendamento não pertence ao usuário"}
            
            if agendamento.status == 'cancelado':
                return {"erro": "Agendamento já foi cancelado"}
            
            if agendamento.status == 'finalizado':
                return {"erro": "Não é possível cancelar um agendamento finalizado"}
            
            # Calcula taxa de cancelamento
            servico = ServicoModel.query.get(agendamento.id_servico)
            taxa = 0.0
            
            if not agendamento.pode_cancelar_gratuito():
                taxa = agendamento.calcular_taxa_cancelamento(float(servico.valor))
            
            # Atualiza status
            agendamento.atualizar(status='cancelado', taxa_cancelamento=taxa)
            
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
        """Lista horários disponíveis para um profissional"""
        
        try:
            profissional = ProfissionalModel.query.get(profissional_id)
            if not profissional:
                return {"erro": "Profissional não encontrado"}
            
            agendamentos = AgendamentoModel.find_by_profissional_data(profissional_id, data)
            
            horarios_disponiveis = []
            horarios_ocupados = set()
            
            # Marca horários ocupados
            for agendamento in agendamentos:
                servico = ServicoModel.query.get(agendamento.id_servico)
                duracao = servico.horario_duracao if servico.horario_duracao else 60
                
                inicio = agendamento.dt_atendimento
                fim = inicio + timedelta(minutes=duracao)
                
                slot_atual = inicio
                while slot_atual < fim:
                    horarios_ocupados.add(slot_atual.strftime("%H:%M"))
                    slot_atual += timedelta(minutes=30)
            
            # Gera horários disponíveis
            data_completa = datetime.combine(data, time(AgendamentoService.HORA_ABERTURA))
            
            while data_completa.hour < AgendamentoService.HORA_FECHAMENTO:
                # Pula horário de almoço
                if (data_completa.hour >= AgendamentoService.HORA_ALMOCO_INICIO and 
                    data_completa.hour < AgendamentoService.HORA_ALMOCO_FIM):
                    data_completa += timedelta(minutes=30)
                    continue
                
                horario_str = data_completa.strftime("%H:%M")
                
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
        """Lista agendamentos de um usuário"""
        
        try:
            agendamentos = AgendamentoModel.find_by_user(user_id)
            
            if status:
                agendamentos = [ag for ag in agendamentos if ag.status == status]
            
            if data_inicio:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento >= data_inicio]
            
            if data_fim:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento <= data_fim]
            
            agendamentos_detalhados = []
            for agendamento in agendamentos:
                ag_dict = agendamento.to_dict()
                
                servico = ServicoModel.query.get(agendamento.id_servico)
                if servico:
                    ag_dict['servico'] = {
                        'descricao': servico.descricao,
                        'valor': float(servico.valor),
                        'duracao': servico.horario_duracao
                    }
                
                profissional = ProfissionalModel.query.get(agendamento.id_profissional)
                if profissional:
                    ag_dict['profissional'] = {
                        'nome': profissional.nome
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
        """Valida dados básicos"""
        
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
        """Verifica horário de funcionamento"""
        
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
        """Verifica disponibilidade do profissional"""
        
        agendamentos_conflito = AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.status != 'cancelado',
            AgendamentoModel.dt_atendimento < dt_fim
        ).all()
        
        for agendamento in agendamentos_conflito:
            servico = ServicoModel.query.get(agendamento.id_servico)
            duracao = servico.horario_duracao if servico.horario_duracao else 60
            ag_fim = agendamento.dt_atendimento + timedelta(minutes=duracao)
            
            if not (dt_fim <= agendamento.dt_atendimento or dt_inicio >= ag_fim):
                return False
        
        return True