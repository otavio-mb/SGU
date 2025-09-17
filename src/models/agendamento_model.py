# importação das bibliotecas necessárias
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from src import db
from . import usuario_model, profissional_model, servicos_model

# criação da tabela de agendamentos
class AgendamentoModel(db.Model):

    __tablename__ = 'tb_agendamentos'
    
    # Campos principais
    id = Column(Integer, primary_key=True, autoincrement=True)
    dt_agendamento = Column(DateTime, nullable=False, default=datetime.utcnow)
    dt_atendimento = Column(DateTime, nullable=False)
    
    # Chaves estrangeiras
    id_user = Column(Integer, ForeignKey('tb_usuario.id'), nullable=False)
    id_profissional = Column(Integer, ForeignKey('tb_profissional.id'), nullable=False)
    id_servico = Column(Integer, ForeignKey('tb_servico.id'), nullable=False)
    
    # Campos adicionais
    status = Column(String(20), nullable=False, default='agendado')
    observacoes = Column(Text, nullable=True)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0.00)
    taxa_cancelamento = Column(Numeric(10, 2), nullable=True, default=0.00)
    
    # Relacionamentos
    usuario = relationship("UsuarioModel", backref="agendamentos")
    profissional = relationship("ProfissionalModel", backref="agendamentos")
    servico = relationship("ServicoModel", backref="agendamentos")
    
    # Função de colocar em um dicionário cada coluna da tabela.
    def to_dict(self):

        return {
            'id': self.id,
            'dt_agendamento': self.dt_agendamento.isoformat() if self.dt_agendamento else None,
            'dt_atendimento': self.dt_atendimento.isoformat() if self.dt_atendimento else None,
            'id_user': self.id_user,
            'id_profissional': self.id_profissional,
            'id_servico': self.id_servico,
            'status': self.status,
            'observacoes': self.observacoes,
            'valor_total': float(self.valor_total) if self.valor_total else 0.0,
            'taxa_cancelamento': float(self.taxa_cancelamento) if self.taxa_cancelamento else 0.0
        }
    
    # Função para salvar um agendamento e feedback caso dê erro
    def salvar(self):

        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao salvar agendamento: {str(e)}")
    
    # Função para atualizar algum agendamento e dar algum feedback de erro.
    def atualizar(self, **kwargs):

        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao atualizar agendamento: {str(e)}")
    
    # Função para deletar e dar algum feedback de erro.
    def deletar(self):

        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao deletar agendamento: {str(e)}")
    
    # Função para poder cancelar algum agendamento que se for em menos de duas horas, vai ser gratuito
    def pode_cancelar_gratuito(self):

        agora = datetime.utcnow()
        diferenca = self.dt_atendimento - agora
        return diferenca.total_seconds() >= 7200  # 2 horas = 7200 segundos
    
    # Função para calcular a taxa do cancelamento
    def calcular_taxa_cancelamento(self, valor_servico):

        agora = datetime.utcnow()
        diferenca = self.dt_atendimento - agora
        minutos_antecedencia = diferenca.total_seconds() / 60
        # Calcula em relação ao valor do serviço e a porcentagem da taxa, que começa em 40% e aumenta em 5% em relação da quantidade de tempo, até 50%
        if minutos_antecedencia >= 120:  # 2 horas ou mais
            return 0.0
        elif minutos_antecedencia >= 90:  # 1h30min
            return valor_servico * 0.40
        elif minutos_antecedencia >= 60:  # 1h
            return valor_servico * 0.45
        elif minutos_antecedencia >= 30:  # 30min
            return valor_servico * 0.50
        else:  # Menos de 30min
            return valor_servico  # 100% do valor
    
    #método para listar pelo id do agendamento
    @staticmethod
    def find_by_id(agendamento_id):

        return AgendamentoModel.query.filter_by(id=agendamento_id).first()
    #método para listar pelo id do usuário
    @staticmethod
    def find_by_user(user_id):

        return AgendamentoModel.query.filter_by(id_user=user_id).all()
    #método para listar pelo id do profissional
    @staticmethod
    def find_by_profissional_data(profissional_id, data):

        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())
        
        return AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.dt_atendimento.between(inicio_dia, fim_dia),
            AgendamentoModel.status != 'cancelado'
        ).order_by(AgendamentoModel.dt_atendimento).all()
    #método para filtrar os conflitos os cancelamentos no agendamento
    @staticmethod
    def find_conflitos_horario(profissional_id, dt_inicio, dt_fim):

        return AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.status != 'cancelado',
            AgendamentoModel.dt_atendimento < dt_fim,
            # Assumindo que temos um campo dt_fim ou calculamos baseado na duração
        ).all()