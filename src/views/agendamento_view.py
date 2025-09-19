# src/views/agendamento_view.py

from flask_restful import Resource
from flask import request, jsonify, make_response
from src.services.agendamento_services import AgendamentoService
from src.models.agendamento_model import AgendamentoModel
from src import api
from datetime import datetime
from functools import wraps

class AgendamentoList(Resource):
    """Gerencia listagem e criação de agendamentos"""
    
    def get(self):
        """Lista agendamentos do usuário autenticado"""
        try:
            # Pega parâmetros de query
            status = request.args.get('status')
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            
            # Converte datas se fornecidas
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio)
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim)
            
            resultado = AgendamentoService.listar_agendamentos_usuario(
                user_id=request.user_id,
                status=status,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({"mensagem": str(e)}), 500
            )
    
    def post(self):
        """Cria novo agendamento"""
        try:
            dados = request.json
            
            # Validação básica
            campos_obrigatorios = ['dt_atendimento', 'id_profissional', 'servicos_ids']
            for campo in campos_obrigatorios:
                if campo not in dados or not dados[campo]:
                    return make_response(
                        jsonify({'mensagem': f'Campo {campo} é obrigatório'}), 400
                    )
            
            # Converte string para datetime
            dt_atendimento = datetime.fromisoformat(dados['dt_atendimento'])
            
            # Cria agendamento
            resultado = AgendamentoService.criar_agendamento(
                dt_atendimento=dt_atendimento,
                id_user=request.user_id,
                id_profissional=dados['id_profissional'],
                servicos_ids=dados['servicos_ids'],
                observacoes=dados.get('observacoes')
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(
                jsonify({
                    'mensagem': 'Agendamento criado com sucesso',
                    'dados': resultado
                }), 201
            )
            
        except ValueError as e:
            return make_response(
                jsonify({'mensagem': f'Data inválida: {str(e)}'}), 400
            )
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao criar agendamento: {str(e)}'}), 500
            )


class AgendamentoDetail(Resource):
    """Gerencia operações de um agendamento específico"""
    
    def get(self, id):
        """Busca agendamento por ID"""
        try:
            agendamento = AgendamentoModel.find_by_id(id)
            
            if not agendamento:
                return make_response(
                    jsonify({'mensagem': 'Agendamento não encontrado'}), 404
                )
            
            # Verifica se o agendamento pertence ao usuário
            if agendamento.id_user != request.user_id:
                return make_response(
                    jsonify({'mensagem': 'Acesso negado'}), 403
                )
            
            return make_response(
                jsonify({'agendamento': agendamento.to_dict()}), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao buscar agendamento: {str(e)}'}), 500
            )
    
    def put(self, id):
        """Atualiza agendamento (apenas observações e status)"""
        try:
            agendamento = AgendamentoModel.find_by_id(id)
            
            if not agendamento:
                return make_response(
                    jsonify({'mensagem': 'Agendamento não encontrado'}), 404
                )
            
            # Verifica se o agendamento pertence ao usuário
            if agendamento.id_user != request.user_id:
                return make_response(
                    jsonify({'mensagem': 'Acesso negado'}), 403
                )
            
            dados = request.json
            
            # Permite atualizar apenas observações
            if 'observacoes' in dados:
                agendamento.atualizar(observacoes=dados['observacoes'])
            
            return make_response(
                jsonify({
                    'mensagem': 'Agendamento atualizado',
                    'agendamento': agendamento.to_dict()
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao atualizar agendamento: {str(e)}'}), 500
            )
    
    def delete(self, id):
        """Cancela agendamento"""
        try:
            resultado = AgendamentoService.cancelar_agendamento(
                agendamento_id=id,
                user_id=request.user_id
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(
                jsonify({
                    'mensagem': 'Agendamento cancelado',
                    'dados': resultado
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao cancelar agendamento: {str(e)}'}), 500
            )


class HorariosDisponiveis(Resource):
    """Lista horários disponíveis para agendamento"""
    
    def get(self):
        """Lista horários disponíveis para um profissional em uma data"""
        try:
            # Pega parâmetros
            profissional_id = request.args.get('profissional_id', type=int)
            data = request.args.get('data')
            
            if not profissional_id or not data:
                return make_response(
                    jsonify({
                        'mensagem': 'Parâmetros profissional_id e data são obrigatórios'
                    }), 400
                )
            
            # Converte data
            data_obj = datetime.fromisoformat(data).date()
            
            resultado = AgendamentoService.listar_horarios_disponiveis(
                profissional_id=profissional_id,
                data=data_obj
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 200)
            
        except ValueError:
            return make_response(
                jsonify({'mensagem': 'Formato de data inválido'}), 400
            )
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao listar horários: {str(e)}'}), 500
            )


class AgendamentosProfissional(Resource):
    """Lista agendamentos de um profissional (para admin/profissional)"""
    
    def get(self, profissional_id):
        """Lista agendamentos de um profissional em uma data"""
        try:
            data = request.args.get('data')
            
            if not data:
                # Se não especificar data, pega hoje
                data_obj = datetime.now().date()
            else:
                data_obj = datetime.fromisoformat(data).date()
            
            agendamentos = AgendamentoModel.find_by_profissional_data(
                profissional_id=profissional_id,
                data=data_obj
            )
            
            agendamentos_list = []
            for ag in agendamentos:
                ag_dict = ag.to_dict()
                
                # Adiciona informações do cliente
                from src.models.usuario_model import UsuarioModel
                usuario = UsuarioModel.query.get(ag.id_user)
                if usuario:
                    ag_dict['cliente'] = {
                        'nome': usuario.nome,
                        'telefone': usuario.telefone
                    }
                
                # Adiciona informações do serviço
                from src.models.servicos_model import ServicoModel
                servico = ServicoModel.query.get(ag.id_servico)
                if servico:
                    ag_dict['servico'] = {
                        'descricao': servico.descricao,
                        'duracao': servico.horario_duracao
                    }
                
                agendamentos_list.append(ag_dict)
            
            return make_response(
                jsonify({
                    'data': data_obj.isoformat(),
                    'profissional_id': profissional_id,
                    'agendamentos': agendamentos_list,
                    'total': len(agendamentos_list)
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao listar agendamentos: {str(e)}'}), 500
            )


class ProximosAgendamentos(Resource):
    """Lista próximos agendamentos do usuário"""
    
    def get(self):
        """Lista próximos agendamentos do usuário logado"""
        try:
            # Busca apenas agendamentos futuros e ativos
            agora = datetime.utcnow()
            
            resultado = AgendamentoService.listar_agendamentos_usuario(
                user_id=request.user_id,
                status='agendado',
                data_inicio=agora
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            # Ordena por data mais próxima
            if resultado.get('agendamentos'):
                resultado['agendamentos'].sort(
                    key=lambda x: x['dt_atendimento']
                )
                
                # Pega apenas os próximos 5
                resultado['agendamentos'] = resultado['agendamentos'][:5]
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao listar próximos agendamentos: {str(e)}'}), 500
            )


# Registra as rotas
api.add_resource(AgendamentoList, '/api/agendamentos')
api.add_resource(AgendamentoDetail, '/api/agendamentos/<int:id>')
api.add_resource(HorariosDisponiveis, '/api/agendamentos/horarios-disponiveis')
api.add_resource(AgendamentosProfissional, '/api/agendamentos/profissional/<int:profissional_id>')
api.add_resource(ProximosAgendamentos, '/api/agendamentos/proximos')