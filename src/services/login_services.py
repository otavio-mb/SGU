from ..models.usuario_model import UsuarioModel
from ..models.login_model import LoginModel
from src import db
import jwt
from datetime import datetime, timedelta
from flask import current_app


def autenticar_usuario(email, senha):
    """Autentica um usuário e retorna um token JWT"""
    try:
        # Busca usuário pelo email
        usuario = UsuarioModel.query.filter_by(email=email).first()
        
        if not usuario:
            return {"erro": "Email ou senha incorretos"}
        
        # Verifica a senha
        if not usuario.verificar_senha(senha):
            return {"erro": "Email ou senha incorretos"}
        
        # Gera token JWT
        payload = {
            'user_id': usuario.id,
            'email': usuario.email,
            'exp': datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
        }
        
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Registra o login
        login_record = LoginModel(email=email, senha="")  # Não armazena senha real
        db.session.add(login_record)
        db.session.commit()
        
        return {
            "sucesso": True,
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            }
        }
        
    except Exception as e:
        return {"erro": f"Erro na autenticação: {str(e)}"}


def verificar_token(token):
    """Verifica se um token JWT é válido"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return {"valido": True, "user_id": payload['user_id']}
    except jwt.ExpiredSignatureError:
        return {"valido": False, "erro": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"valido": False, "erro": "Token inválido"}


def logout_usuario(token):
    """Realiza logout do usuário (pode ser usado para blacklist de tokens)"""
    # Em uma implementação mais robusta, você poderia adicionar o token
    # a uma blacklist no Redis ou banco de dados
    return {"sucesso": True, "mensagem": "Logout realizado com sucesso"}


def trocar_senha(user_id, senha_atual, senha_nova):
    """Permite que o usuário troque sua senha"""
    try:
        usuario = UsuarioModel.query.get(user_id)
        
        if not usuario:
            return {"erro": "Usuário não encontrado"}
        
        # Verifica senha atual
        if not usuario.verificar_senha(senha_atual):
            return {"erro": "Senha atual incorreta"}
        
        # Atualiza para nova senha
        usuario.gen_senha(senha_nova)
        db.session.commit()
        
        return {"sucesso": True, "mensagem": "Senha alterada com sucesso"}
        
    except Exception as e:
        db.session.rollback()
        return {"erro": f"Erro ao trocar senha: {str(e)}"}


def recuperar_senha(email):
    """Envia email para recuperação de senha (implementação simplificada)"""
    try:
        usuario = UsuarioModel.query.filter_by(email=email).first()
        
        if not usuario:
            # Por segurança, não revelamos se o email existe ou não
            return {"sucesso": True, "mensagem": "Se o email existir, instruções serão enviadas"}
        
        # Aqui você implementaria o envio de email real
        # Por exemplo, usando Flask-Mail ou outro serviço
        
        # Gera token temporário para reset
        reset_token = jwt.encode(
            {
                'user_id': usuario.id,
                'action': 'reset_password',
                'exp': datetime.utcnow() + timedelta(hours=1)
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Em produção, você enviaria este token por email
        # Por enquanto, retornamos como resposta (apenas para desenvolvimento)
        return {
            "sucesso": True,
            "mensagem": "Instruções enviadas por email",
            "reset_token": reset_token  # Remover em produção!
        }
        
    except Exception as e:
        return {"erro": f"Erro ao processar recuperação: {str(e)}"}