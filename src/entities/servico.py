from datetime import datetime

class Servico:
    def __init__(self, descricao: str, valor: float, horario_duracao: datetime):
            self.__descricao = descricao
            self.__valor = valor
            self.__horario_duracao = horario_duracao

    ''' Descrição '''

    @property
    def descricao(self):
        return self.__descricao
    
    @descricao.setter
    def descricao(self, descricao):
        self.__descricao = descricao
    

    ''' Valor '''

    @property
    def valor(self):
        return self.__valor
    
    @valor.setter
    def valor(self, valor):
        self.__valor = valor

    
    ''' Horario Duração '''

    @property
    def horario_duracao(self):
        return self.__horario_duracao
    
    @horario_duracao.setter
    def horario_duracao(self, horario_duracao):
        self.__horario_duracao = horario_duracao