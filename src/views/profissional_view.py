# src/views/profissional_view.py

from flask_restful import Resource
from flask import request, jsonify, make_response
from marshmallow import ValidationError, Schema, fields
from src import api, db
from src.services import profissional_services
from src.models.profissional_model import ProfissionalModel
from src.models.agendamento_model import AgendamentoModel
from src.entities.profissional import Profissional
from datetime import datetime, timedelta


# Schema simples para validação (já que o schema estava incorreto no projeto)
class ProfissionalSchema(Schema):
    id = fields.Integer(dump_only=True)
    nome = fields.String(required=True)


class ProfissionalList(Resource):
    """Recurso para listar e criar profissionais"""
    
    def get(self):
        """Lista todos os profissionais"""
        try:
            profissionais = profissional_services.listar_profissionais()
            
            if not profissionais:
                return make_response(
                    jsonify({
                        "mensagem": "Nenhum profissional cadastrado",
                        "profissionais": []
                    }), 200
                )
            
            # Serializa os dados
            resultado = []
            for prof in profissionais:
                # Busca o modelo para obter o ID
                prof_model = ProfissionalModel.query.filter_by(nome=prof.nome).first()
                resultado.append({
                    'id': prof_model.id if prof_model else None,
                    'nome': prof.nome
                })
            
            return make_response(
                jsonify({
                    "profissionais": resultado,
                    "total": len(resultado)
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao listar profissionais: {str(e)}"}), 500
            )
    
    def post(self):
        """Cria um novo profissional"""
        try:
            schema = ProfissionalSchema()
            
            # Valida os dados de entrada
            try:
                dados = schema.load(request.json)
            except ValidationError as err:
                return make_response(
                    jsonify({"erros": err.messages}), 400
                )
            
            # Verifica se já existe um profissional com o mesmo nome
            profissional_existente = ProfissionalModel.query.filter_by(
                nome=dados['nome']
            ).first()
            
            if profissional_existente:
                return make_response(
                    jsonify({"erro": "Já existe um profissional com este nome"}), 400
                )
            
            # Cria a entidade
            novo_profissional = Profissional(nome=dados['nome'])
            
            # Salva no banco
            resultado = profissional_services.cadastrar_profissional(novo_profissional)
            
            return make_response(
                jsonify({
                    "mensagem": "Profissional criado com sucesso",
                    "profissional": {
                        "id": resultado.id,
                        "nome": resultado.nome
                    }
                }), 201
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao criar profissional: {str(e)}"}), 500
            )


class ProfissionalResource(Resource):
    """Recurso para operações específicas de um profissional"""
    
    def get(self, id_profissional):
        """Obtém detalhes de um profissional específico"""
        try:
            profissional = profissional_services.listar_profissional_id(id_profissional)
            
            if not profissional:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Busca informações adicionais
            prof_model = ProfissionalModel.query.get(id_profissional)
            
            # Conta agendamentos
            total_agendamentos = AgendamentoModel.query.filter_by(
                id_profissional=id_profissional
            ).count()
            
            agendamentos_hoje = AgendamentoModel.query.filter(
                AgendamentoModel.id_profissional == id_profissional,
                AgendamentoModel.dt_atendimento >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                AgendamentoModel.dt_atendimento < datetime.now().replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ),
                AgendamentoModel.status == 'agendado'
            ).count()
            
            return make_response(
                jsonify({
                    "profissional": {
                        "id": id_profissional,
                        "nome": profissional.nome
                    },
                    "estatisticas": {
                        "total_agendamentos": total_agendamentos,
                        "agendamentos_hoje": agendamentos_hoje
                    }
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao buscar profissional: {str(e)}"}), 500
            )
    
    def put(self, id_profissional):
        """Atualiza um profissional existente"""
        try:
            schema = ProfissionalSchema()
            
            # Verifica se o profissional existe
            profissional_atual = profissional_services.listar_profissional_id(id_profissional)
            
            if not profissional_atual:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Valida os dados
            try:
                dados = schema.load(request.json)
            except ValidationError as err:
                return make_response(
                    jsonify({"erros": err.messages}), 400
                )
            
            # Verifica se o novo nome já existe (exceto para o próprio profissional)
            profissional_existente = ProfissionalModel.query.filter(
                ProfissionalModel.nome == dados['nome'],
                ProfissionalModel.id != id_profissional
            ).first()
            
            if profissional_existente:
                return make_response(
                    jsonify({"erro": "Já existe outro profissional com este nome"}), 400
                )
            
            # Atualiza o profissional
            profissional_atual.nome = dados['nome']
            resultado = profissional_services.editar_profissional(
                id_profissional, profissional_atual
            )
            
            if not resultado:
                return make_response(
                    jsonify({"erro": "Erro ao atualizar profissional"}), 500
                )
            
            return make_response(
                jsonify({
                    "mensagem": "Profissional atualizado com sucesso",
                    "profissional": {
                        "id": id_profissional,
                        "nome": resultado.nome
                    }
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao atualizar profissional: {str(e)}"}), 500
            )
    
    def delete(self, id_profissional):
        """Exclui um profissional"""
        try:
            # Verifica se o profissional existe
            profissional = profissional_services.listar_profissional_id(id_profissional)
            
            if not profissional:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Tenta excluir (o service já verifica se há agendamentos ativos)
            resultado = profissional_services.excluir_profissional(id_profissional)
            
            if isinstance(resultado, dict) and "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            if not resultado:
                return make_response(
                    jsonify({"erro": "Erro ao excluir profissional"}), 500
                )
            
            return make_response(
                jsonify({"mensagem": "Profissional excluído com sucesso"}), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao excluir profissional: {str(e)}"}), 500
            )


class ProfissionalAgendamentos(Resource):
    """Recurso para listar agendamentos de um profissional"""
    
    def get(self, id_profissional):
        """Lista agendamentos de um profissional"""
        try:
            # Verifica se o profissional existe
            profissional = ProfissionalModel.query.get(id_profissional)
            if not profissional:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Obtém parâmetros de query
            data = request.args.get('data')
            status = request.args.get('status', 'agendado')
            
            # Constrói a query
            query = AgendamentoModel.query.filter_by(id_profissional=id_profissional)
            
            if status:
                query = query.filter_by(status=status)
            
            if data:
                try:
                    data_obj = datetime.fromisoformat(data).date()
                    inicio_dia = datetime.combine(data_obj, datetime.min.time())
                    fim_dia = datetime.combine(data_obj, datetime.max.time())
                    query = query.filter(
                        AgendamentoModel.dt_atendimento.between(inicio_dia, fim_dia)
                    )
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de data inválido"}), 400
                    )
            
            # Ordena por data de atendimento
            agendamentos = query.order_by(AgendamentoModel.dt_atendimento).all()
            
            # Prepara resposta
            resultado = []
            for ag in agendamentos:
                ag_dict = ag.to_dict()
                
                # Adiciona informações do usuário
                if ag.usuario:
                    ag_dict['usuario'] = {
                        'nome': ag.usuario.nome,
                        'telefone': ag.usuario.telefone
                    }
                
                # Adiciona informações do serviço
                if ag.servico:
                    ag_dict['servico'] = {
                        'descricao': ag.servico.descricao,
                        'duracao': ag.servico.horario_duracao
                    }
                
                resultado.append(ag_dict)
            
            return make_response(
                jsonify({
                    "profissional": {
                        "id": profissional.id,
                        "nome": profissional.nome
                    },
                    "agendamentos": resultado,
                    "total": len(resultado)
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({"erro": f"Erro ao listar agendamentos: {str(e)}"}), 500
            )


class ProfissionalDisponibilidade(Resource):
    """Recurso para verificar disponibilidade de um profissional"""
    
    def get(self, id_profissional):
        """Verifica disponibilidade de um profissional em um período"""
        try:
            # Verifica se o profissional existe
            profissional = ProfissionalModel.query.get(id_profissional)
            if not profissional:
                return make_response(
                    jsonify({"erro": "Profissional não encontrado"}), 404
                )
            
            # Obtém parâmetros
            data = request.args.get('data')
            hora_inicio = request.args.get('hora_inicio')
            hora_fim = request.args.get('hora_fim')
            
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
            
            # Se horários específicos foram fornecidos
            if hora_inicio and hora_fim:
                try:
                    dt_inicio = datetime.fromisoformat(f"{data} {hora_inicio}")
                    dt_fim = datetime.fromisoformat(f"{data} {hora_fim}")
                except ValueError:
                    return make_response(
                        jsonify({"erro": "Formato de horário inválido"}), 400
                    )
                
                # Verifica disponibilidade
                from src.services.agendamento_services import AgendamentoService
                disponivel = AgendamentoService._verificar_disponibilidade(
                    id_profissional, dt_inicio, dt_fim
                )
                
                return make_response(
                    jsonify({
                        "profissional": {
                            "id": profissional.id,
                            "nome": profissional.nome
                        },
                        "periodo": {
                            "data": data,
                            "hora_inicio": hora_inicio,
                            "hora_fim": hora_fim
                        },
                        "disponivel": disponivel
                    }), 200
                )
            
            # Caso contrário, retorna todos os horários disponíveis do dia
            from src.services.agendamento_services import AgendamentoService
            resultado = AgendamentoService.listar_horarios_disponiveis(
                id_profissional, data_obj
            )
            
            if "erro" in resultado:
                return make_response(jsonify(resultado), 400)
            
            resultado["profissional"] = {
                "id": profissional.id,
                "nome": profissional.nome
            }
            
            return make_response(jsonify(resultado), 200)
            
        except Exception as e: