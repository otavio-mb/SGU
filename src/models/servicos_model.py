from src import db

class ServicoModel(db.Model):
    __tablename__ = "tb_servico"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    descricao = db.Column(db.String(120), nullable = False)
    valor = db.Column(db.Float, nullable = False)
    horario_duracao = db.Column(db.Float, nullable = False)