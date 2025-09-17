from datetime import datetime

class Agendamento:
    def __init__(self, dt_atendimento, id_user, id_profissional, id_servico, 
                    observacoes=None, valor_total=0.00):
            
        self.__dt_atendimento = dt_atendimento
        self.__id_user = id_user
        self.__id_profissional = id_profissional
        self.__id_servico = id_servico
        self.__observacoes = observacoes
        self.__valor_total = valor_total
        self.__dt_agendamento = datetime.utcnow()
        self.__status = 'agendado'

    ''' dt_atendimento '''

    @property
    def dt_atendimento(self):
        return self.__dt_atendimento
    
    @dt_atendimento.setter
    def dt_atendimento(self, dt_atendimento):
        self.__dt_atendimento = dt_atendimento

    ''' id_user '''

    @property
    def id_user(self):
        return self.__id_user
    
    @id_user.setter
    def id_user(self, id_user):
        self.__id_user = id_user

    ''' id_profissional '''

    @property
    def id_profissional(self):
        return self.__id_profissional
    
    @id_profissional.setter
    def id_profissional(self, id_profissional):
        self.__id_profissional = id_profissional

    ''' id_servico '''

    @property
    def id_servico(self):
        return self.__id_servico
    
    @id_servico.setter
    def id_servico(self, id_servico):
        self.__id_servico = id_servico

    ''' observacoes '''

    @property
    def observacoes(self):
        return self.__observacoes
    
    @observacoes.setter
    def observacoes(self, observacoes):
        self.__observacoes = observacoes

    ''' valor_total '''

    @property
    def valor_total(self):
        return self.__valor_total
    
    @valor_total.setter
    def valor_total(self, valor_total):
        self.__valor_total = valor_total

    ''' dt_agendamento (somente leitura) '''

    @property
    def dt_agendamento(self):
        return self.__dt_agendamento

    ''' status '''

    @property
    def status(self):
        return self.__status
    
    @status.setter
    def status(self, status):
        self.__status = status

    def __str__(self):
        return (
            f"Agendamento("
            f"Atendimento: {self.__dt_atendimento}, "
            f"Usuário: {self.__id_user}, "
            f"Profissional: {self.__id_profissional}, "
            f"Serviço: {self.__id_servico}, "
            f"Observações: {self.__observacoes}, "
            f"Valor Total: R${self.__valor_total:.2f}, "
            f"Data Agendamento: {self.__dt_agendamento}, "
            f"Status: {self.__status})"
        )