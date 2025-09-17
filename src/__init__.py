from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_restful import Api


app = Flask(__name__)
app.config.from_object('connection')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
api = Api(app)
CORS(app)

@app.before_request
def create_tables():
    if request.endpoint == "index":
        db.create_all()

from .models import agendamento_model, login_model, profissional_model, servicos_model, usuario_model

from .views import usuario_view