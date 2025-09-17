from src import ma
from src.models import profissional_model
from marshmallow import fields

class LoginSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = profissional_model.Profissional

        fields = ("id", "nome")

    nome = fields.String(required=True)