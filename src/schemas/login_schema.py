from src import ma
from src.models import login_model
from marshmallow import fields

class LoginSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = login_model.Login

        fields = ("id", "email", "senha")

    email = fields.String(required=True)
    senha = fields.String(required=True)