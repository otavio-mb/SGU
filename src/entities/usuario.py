class Usuario:
    def __init__(self, nome, email, telefone, senha):
        self.__nome = nome
        self.__email = email
        self.__telefone = telefone
        self.__senha = senha

    # GET e SET serão usados para manipular os atríbutos privados (__).

    ''' Nome '''

    @property
    def nome(self):
        return self.__nome
    
    @nome.setter
    def nome(self, nome):
        self.__nome = nome
    

    ''' E-mail '''

    @property # Decorador para não ser como função
    def email(self):
        return self.__email
    
    @email.setter
    def email(self, email):
        self.__email = email

    
    ''' Telefone '''

    @property
    def telefone(self):
        return self.__telefone
    
    @telefone.setter
    def telefone(self, telefone):
        self.__telefone = telefone


    ''' Senha '''

    @property
    def senha(self):
        return self.__senha
    
    @senha.setter
    def senha(self, senha):
        self.__senha = senha
