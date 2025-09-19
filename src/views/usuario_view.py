# src/views/usuario_view.py

from flask_restful import Resource
from flask import request, jsonify, make_response
from src.services import usuario_services
from src.entities.usuario import Usuario
from src.schemas.usuario_schema import UsuarioSchema
from src import api
from functools import wraps

class UsuarioList(Resource):
    """Lista todos os usuários ou cria um novo"""
    
    def get(self):
        """Lista todos os usuários"""
        try:
            usuarios = usuario_services.listar_usuario()
            usuario_schema = UsuarioSchema(many=True)
            
            # Converte entidades para dict
            usuarios_dict = []
            for usuario in usuarios:
                usuarios_dict.append({
                    'nome': usuario.nome,
                    'email': usuario.email,
                    'telefone': usuario.telefone
                })
            
            return make_response(
                jsonify({
                    'usuarios': usuarios_dict,
                    'total': len(usuarios_dict)
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao listar usuários: {str(e)}'}), 500
            )
    
    def post(self):
        """Cadastra novo usuário"""
        try:
            dados = request.json
            
            # Validação dos campos obrigatórios
            campos_obrigatorios = ['nome', 'email', 'telefone', 'senha']
            for campo in campos_obrigatorios:
                if campo not in dados or not dados[campo]:
                    return make_response(
                        jsonify({'mensagem': f'Campo {campo} é obrigatório'}), 400
                    )
            
            # Verifica se email já existe
            usuario_existente = usuario_services.listar_usuario_email(dados['email'])
            if usuario_existente:
                return make_response(
                    jsonify({'mensagem': 'Email já cadastrado'}), 409
                )
            
            # Cria entidade usuario
            usuario_entity = Usuario(
                nome=dados['nome'],
                email=dados['email'],
                telefone=dados['telefone'],
                senha=dados['senha']
            )
            
            # Cadastra no banco
            usuario_cadastrado = usuario_services.cadastrar_usuario(usuario_entity)
            
            return make_response(
                jsonify({
                    'mensagem': 'Usuário cadastrado com sucesso',
                    'usuario': {
                        'id': usuario_cadastrado.id,
                        'nome': usuario_cadastrado.nome,
                        'email': usuario_cadastrado.email,
                        'telefone': usuario_cadastrado.telefone
                    }
                }), 201
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao cadastrar usuário: {str(e)}'}), 500
            )


class UsuarioDetail(Resource):
    """Gerencia operações de um usuário específico"""
    
    def get(self, id):
        """Busca usuário por ID"""
        try:
            # Verifica se usuário pode acessar este recurso
            if request.user_id != id:
                return make_response(
                    jsonify({'mensagem': 'Acesso negado'}), 403
                )
            
            usuario = usuario_services.listar_usuario_id(id)
            
            if not usuario:
                return make_response(
                    jsonify({'mensagem': 'Usuário não encontrado'}), 404
                )
            
            return make_response(
                jsonify({
                    'usuario': {
                        'id': id,
                        'nome': usuario.nome,
                        'email': usuario.email,
                        'telefone': usuario.telefone
                    }
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao buscar usuário: {str(e)}'}), 500
            )
    
    def put(self, id):
        """Atualiza usuário"""
        try:
            # Verifica se usuário pode atualizar este recurso
            if request.user_id != id:
                return make_response(
                    jsonify({'mensagem': 'Acesso negado'}), 403
                )
            
            dados = request.json
            
            # Busca usuário atual
            usuario_atual = usuario_services.listar_usuario_id(id)
            if not usuario_atual:
                return make_response(
                    jsonify({'mensagem': 'Usuário não encontrado'}), 404
                )
            
            # Cria entidade com dados atualizados
            usuario_entity = Usuario(
                nome=dados.get('nome', usuario_atual.nome),
                email=usuario_atual.email,  # Email não pode ser alterado
                telefone=dados.get('telefone', usuario_atual.telefone),
                senha=dados.get('senha', '')  # Senha opcional
            )
            
            # Atualiza no banco
            usuario_atualizado = usuario_services.editar_usuario(id, usuario_entity)
            
            if not usuario_atualizado:
                return make_response(
                    jsonify({'mensagem': 'Erro ao atualizar usuário'}), 500
                )
            
            return make_response(
                jsonify({
                    'mensagem': 'Usuário atualizado com sucesso',
                    'usuario': {
                        'id': id,
                        'nome': usuario_atualizado.nome,
                        'email': usuario_atualizado.email,
                        'telefone': usuario_atualizado.telefone
                    }
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao atualizar usuário: {str(e)}'}), 500
            )
    
    def delete(self, id):
        """Exclui usuário"""
        try:
            # Verifica se usuário pode excluir este recurso
            if request.user_id != id:
                return make_response(
                    jsonify({'mensagem': 'Acesso negado'}), 403
                )
            
            # Verifica se usuário tem agendamentos ativos
            from src.models.agendamento_model import AgendamentoModel
            agendamentos_ativos = AgendamentoModel.query.filter_by(
                id_user=id,
                status='agendado'
            ).first()
            
            if agendamentos_ativos:
                return make_response(
                    jsonify({
                        'mensagem': 'Não é possível excluir usuário com agendamentos ativos'
                    }), 409
                )
            
            sucesso = usuario_services.excluir_usuario(id)
            
            if not sucesso:
                return make_response(
                    jsonify({'mensagem': 'Usuário não encontrado'}), 404
                )
            
            return make_response(
                jsonify({'mensagem': 'Usuário excluído com sucesso'}), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao excluir usuário: {str(e)}'}), 500
            )


class UsuarioPerfil(Resource):
    """Gerencia o perfil do usuário logado"""
    
    def get(self):
        """Retorna perfil do usuário logado"""
        try:
            usuario = usuario_services.listar_usuario_id(request.user_id)
            
            if not usuario:
                return make_response(
                    jsonify({'mensagem': 'Usuário não encontrado'}), 404
                )
            
            # Busca estatísticas do usuário
            from src.models.agendamento_model import AgendamentoModel
            agendamentos = AgendamentoModel.find_by_user(request.user_id)
            
            total_agendamentos = len(agendamentos)
            agendamentos_ativos = len([a for a in agendamentos if a.status == 'agendado'])
            agendamentos_concluidos = len([a for a in agendamentos if a.status == 'finalizado'])
            agendamentos_cancelados = len([a for a in agendamentos if a.status == 'cancelado'])
            
            return make_response(
                jsonify({
                    'perfil': {
                        'id': request.user_id,
                        'nome': usuario.nome,
                        'email': usuario.email,
                        'telefone': usuario.telefone
                    },
                    'estatisticas': {
                        'total_agendamentos': total_agendamentos,
                        'agendamentos_ativos': agendamentos_ativos,
                        'agendamentos_concluidos': agendamentos_concluidos,
                        'agendamentos_cancelados': agendamentos_cancelados
                    }
                }), 200
            )
            
        except Exception as e:
            return make_response(
                jsonify({'mensagem': f'Erro ao buscar perfil: {str(e)}'}), 500
            )


# Registra as rotas
api.add_resource(UsuarioList, '/api/usuarios')
api.add_resource(UsuarioDetail, '/api/usuarios/<int:id>')
api.add_resource(UsuarioPerfil, '/api/usuarios/perfil')