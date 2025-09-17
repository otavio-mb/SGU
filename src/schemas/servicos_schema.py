from src import ma
from src.models import servicos_model
from marshmallow import fields

class ServicosSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = servicos_model.Servicos

        fields = ("id", "descricao", "valor")
    
    descricao = fields.String(required = True)
    valor = fields.Boolean(required = True)