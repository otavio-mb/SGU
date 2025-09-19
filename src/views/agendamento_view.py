from flask_restful import Resource
from flask import request, jsonify, make_response
from src.services.agendamento_services import AgendamentoService
from src.models.agendamento_model import AgendamentoModel
from src import api
from datetime import datetime
import jwt
from functools import wraps


def token_required(f):
    """Decorator para verificar token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return make_response(
                jsonify({'message': 'Token ausente'}), 401
            )
        
        try:
            # Remove 'Bearer ' do início do token se presente
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            from flask import current_app
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return make_response(
                jsonify({'message': 'Token expirado'}), 401
            )
        except jwt.InvalidTokenError:
            return make_response(
                jsonify({'message': 'Token inválido'}), 401
            )
        
        return f(*args, **kwargs)
    return decorated


class AgendamentoList(Resource):
    """Gerencia listagem e criação de agendamentos"""
    
    @token_required
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
                jsonify({"message": str(e)}), 500
            )
    
    @token_required
    def post(self):
        """Cria novo agendamento"""
        try:
            dados = request.json
            
            # Validação básica
            campos_obrigatorios = ['dt_atendimento', 'id_profissional', 'servicos_ids']
            for campo in