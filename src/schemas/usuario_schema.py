from src import ma
from src.models import usuario_model
from marshmallow import fields

class UsuarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = usuario_model.UsuarioModel
        fields = ("id", "nome", "email", "telefone", "senha")

    nome = fields.String(required=True)
    email = fields.String(required=True)
    telefone = fields.String(required=True)
    senha = fields.String(required=True)
