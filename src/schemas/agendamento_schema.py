from src import ma
from src.models import agendamento_model
from marshmallow import fields

class AgendamentoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = agendamento_model.Agendamento

        fields = ("id", "dt_agendamento", "dt_atendimento", "User_idUser", "Servicos_idServicos", "Profissional_idProfissional")

    dt_agendamento = fields.DateTime(required=True)
    dt_atendimento = fields.DateTime(required=True)
    Uder_idUser = fields.Integer(required=True)
    Servicos_idServicos = fields.Integer(required=True)
    Profissional_idProfissional = fields.Integer(required=True)