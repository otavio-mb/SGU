# src/views/agendamento_view.py

from flask_restful import Resource
from flask import request, jsonify, make_response
from marshmallow import ValidationError
from datetime import datetime
from src import api, db
from src.services.agendamento_services import AgendamentoService
from src.models.agendamento_model import AgendamentoModel
from src.models.usuario_model import UsuarioModel
from src.models.profissional_model import ProfissionalModel
from src.models.servicos_model import ServicoModel


class AgendamentoList(Resource):
    """Recurso para listar e criar agendamentos"""
    
    def get(self):
        """Lista todos os agendamentos com filtros opcionais"""
        try:
            # Obtém parâmetros de query
            user_id = request.args.get('user_id', type=int)
            profissional_id = request.args.get('profissional_id', type=int)
            status = request.args.get('status')
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            
            # Constrói query base
            query = AgendamentoModel.query
            
            # Aplica filtros
            if user_id:
                query = query.filter_by(id_user=user_id)
            
            if profissional_id:
                query = query.filter_by(id_profissional=profissional_id)
            
            if status:
                query = query.filter_by(status=status)
            
            if data_inicio:
                try:
                    dt_inicio = datetime.fromisoformat(data_inicio)
                    query = query.filter(AgendamentoModel.dt_atendimento >= dt_inicio)
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de data_inicio inválido"}), 400
                    )
            
            if data_fim:
                try:
                    dt_fim = datetime.fromisoformat(data_fim)
                    query = query.filter(AgendamentoModel.dt_atendimento <= dt_fim)
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de data_fim inválido"}), 400
                    )
            
            # Executa query
            agendamentos = query.order_by(AgendamentoModel.dt_atendimento.desc()).all()
            
            # Prepara resposta detalhada
            resultado = []
            for ag in agendamentos:
                ag_dict = ag.to_dict()
                
                # Adiciona informações relacionadas
                if ag.usuario:
                    ag_dict['usuario'] = {
                        'id': ag.usuario.id,
                        'nome': ag.usuario.nome,
                        'email': ag.usuario.email,
                        'telefone': ag.usuario.telefone
                    }
                
                if ag.profissional:
                    ag_dict['profissional'] = {
                        'id': ag.profissional.id,
                        'nome': ag.profissional.nome
                    }
                
                if ag.servico:
                    ag_dict['servico'] = {
                        'id': ag.servico.id,
                        'descricao': ag.servico.descricao,
                        'valor': float(ag.servico.valor),
                        'duracao': ag.servico.horario_duracao
                    }
                
                resultado.append(ag_dict)
            
            return make_response(
                jsonify({
                    "agendamentos": resultado,
                    "total": len(resultado)
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao listar agendamentos: {str(e)}"}), 500
            )
    
    def post(self):
        """Cria um novo agendamento"""
        try:
            dados = request.json
            
            # Validação dos campos obrigatórios
            campos_obrigatorios = ['dt_atendimento', 'id_user', 'id_profissional', 'servicos_ids']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    return make_response(
                        jsonify({"erro": f"Campo '{campo}' é obrigatório"}), 400
                    )
            
            # Converte string de data para datetime
            try:
                dt_atendimento = datetime.fromisoformat(dados['dt_atendimento'])
            except (ValueError, TypeError):
                return make_response(
                    jsonify({"erro": "Formato de data/hora inválido"}), 400
                )
            
            # Valida se o usuário existe
            usuario = UsuarioModel.query.get(dados['id_user'])
            if not usuario:
                return make_response(
                    jsonify({"erro": "Usuário não encontrado"}), 404
                )
            
            # Valida se o profissional existe
            profissional = ProfissionalModel.query.get(dados['id_profissional'])
            if not profissional:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Valida se os serviços existem
            servicos_ids = dados.get('servicos_ids', [])
            if not isinstance(servicos_ids, list) or len(servicos_ids) == 0:
                return make_response(
                    jsonify({"erro": "Lista de serviços inválida ou vazia"}), 400
                )
            
            for servico_id in servicos_ids:
                servico = ServicoModel.query.get(servico_id)
                if not servico:
                    return make_response(
                        jsonify({"erro": f"Serviço com ID {servico_id} não encontrado"}), 404
                    )
            
            # Chama o service para criar o agendamento
            resultado = AgendamentoService.criar_agendamento(
                dt_atendimento=dt_atendimento,
                id_user=dados['id_user'],
                id_profissional=dados['id_profissional'],
                servicos_ids=servicos_ids,
                observacoes=dados.get('observacoes')
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 201)
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao criar agendamento: {str(e)}"}), 500
            )


class AgendamentoResource(Resource):
    """Recurso para operações específicas de um agendamento"""
    
    def get(self, id_agendamento):
        """Obtém detalhes de um agendamento específico"""
        try:
            agendamento = AgendamentoModel.find_by_id(id_agendamento)
            
            if not agendamento:
                return make_response(
                    jsonify({"erro": "Agendamento não encontrado"}), 404
                )
            
            # Prepara resposta detalhada
            resultado = agendamento.to_dict()
            
            # Adiciona informações relacionadas
            if agendamento.usuario:
                resultado['usuario'] = {
                    'id': agendamento.usuario.id,
                    'nome': agendamento.usuario.nome,
                    'email': agendamento.usuario.email,
                    'telefone': agendamento.usuario.telefone
                }
            
            if agendamento.profissional:
                resultado['profissional'] = {
                    'id': agendamento.profissional.id,
                    'nome': agendamento.profissional.nome
                }
            
            if agendamento.servico:
                resultado['servico'] = {
                    'id': agendamento.servico.id,
                    'descricao': agendamento.servico.descricao,
                    'valor': float(agendamento.servico.valor),
                    'duracao': agendamento.servico.horario_duracao
                }
            
            # Adiciona informações sobre cancelamento
            resultado['pode_cancelar_gratuito'] = agendamento.pode_cancelar_gratuito()
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao buscar agendamento: {str(e)}"}), 500
            )
    
    def put(self, id_agendamento):
        """Atualiza um agendamento existente"""
        try:
            agendamento = AgendamentoModel.find_by_id(id_agendamento)
            
            if not agendamento:
                return make_response(
                    jsonify({"erro": "Agendamento não encontrado"}), 404
                )
            
            dados = request.json
            
            # Verifica se o agendamento pode ser modificado
            if agendamento.status in ['finalizado', 'cancelado']:
                return make_response(
                    jsonify({"erro": f"Não é possível modificar agendamento {agendamento.status}"}), 400
                )
            
            # Campos que podem ser atualizados
            campos_atualizaveis = ['dt_atendimento', 'observacoes', 'status']
            atualizacoes = {}
            
            for campo in campos_atualizaveis:
                if campo in dados:
                    if campo == 'dt_atendimento':
                        try:
                            atualizacoes[campo] = datetime.fromisoformat(dados[campo])
                            
                            # Verifica disponibilidade para nova data
                            nova_dt = atualizacoes[campo]
                            servico = ServicoModel.query.get(agendamento.id_servico)
                            duracao = servico.horario_duracao if servico else 60
                            dt_fim = nova_dt + timedelta(minutes=duracao)
                            
                            if not AgendamentoService._verificar_disponibilidade(
                                agendamento.id_profissional, nova_dt, dt_fim
                            ):
                                return make_response(
                                    jsonify({"erro": "Novo horário não está disponível"}), 400
                                )
                        except ValueError:
                            return make_response(
                                jsonify({"erro": "Formato de data/hora inválido"}), 400
                            )
                    else:
                        atualizacoes[campo] = dados[campo]
            
            # Atualiza o agendamento
            agendamento.atualizar(**atualizacoes)
            
            return make_response(
                jsonify({
                    "mensagem": "Agendamento atualizado com sucesso",
                    "agendamento": agendamento.to_dict()
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao atualizar agendamento: {str(e)}"}), 500
            )
    
    def delete(self, id_agendamento):
        """Cancela um agendamento"""
        try:
            # Obtém user_id dos parâmetros ou do corpo da requisição
            user_id = request.args.get('user_id', type=int)
            if not user_id and request.json:
                user_id = request.json.get('user_id')
            
            if not user_id:
                return make_response(
                    jsonify({"erro": "ID do usuário é obrigatório para cancelamento"}), 400
                )
            
            # Chama o service para cancelar
            resultado = AgendamentoService.cancelar_agendamento(id_agendamento, user_id)
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao cancelar agendamento: {str(e)}"}), 500
            )


class HorariosDisponiveis(Resource):
    """Recurso para consultar horários disponíveis"""
    
    def get(self):
        """Lista horários disponíveis para um profissional em uma data"""
        try:
            profissional_id = request.args.get('profissional_id', type=int)
            data = request.args.get('data')
            
            if not profissional_id:
                return make_response(
                    jsonify({"erro": "ID do profissional é obrigatório"}), 400
                )
            
            if not data:
                return make_response(
                    jsonify({"erro": "Data é obrigatória"}), 400
                )
            
            try:
                data_obj = datetime.fromisoformat(data).date()
            except ValueError:
                return make_response(
                    jsonify({"erro": "Formato de data inválido"}), 400
                )
            
            # Chama o service para obter horários
            resultado = AgendamentoService.listar_horarios_disponiveis(
                profissional_id, data_obj
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao buscar horários: {str(e)}"}), 500
            )


class AgendamentosPorUsuario(Resource):
    """Recurso para listar agendamentos de um usuário específico"""
    
    def get(self, id_usuario):
        """Lista todos os agendamentos de um usuário"""
        try:
            # Verifica se o usuário existe
            usuario = UsuarioModel.query.get(id_usuario)
            if not usuario:
                return make_response(
                    jsonify({"erro": "Usuário não encontrado"}), 404
                )
            
            # Obtém parâmetros opcionais
            status = request.args.get('status')
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            
            # Converte datas se fornecidas
            dt_inicio = None
            dt_fim = None
            
            if data_inicio:
                try:
                    dt_inicio = datetime.fromisoformat(data_inicio)
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de data_inicio inválido"}), 400
                    )
            
            if data_fim:
                try:
                    dt_fim = datetime.fromisoformat(data_fim)
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de data_fim inválido"}), 400
                    )
            
            # Chama o service
            resultado = AgendamentoService.listar_agendamentos_usuario(
                id_usuario, status, dt_inicio, dt_fim
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao listar agendamentos: {str(e)}"}), 500
            )


# Registra as rotas
api.add_resource(AgendamentoList, '/agendamentos')
api.add_resource(AgendamentoResource, '/agendamentos/<int:id_agendamento>')
api.add_resource(HorariosDisponiveis, '/agendamentos/horarios-disponiveis')
api.add_resource(AgendamentosPorUsuario, '/usuarios/<int:id_usuario>/agendamentos')