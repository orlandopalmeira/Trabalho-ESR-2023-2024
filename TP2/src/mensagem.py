import random
import datetime
import pickle


class Mensagem:
    #! WIP
    video=1
    control=2
    vizinho=3
    rota=4
    pedido=5
    resposta=6

    def __init__(self, tipo:int, origem:str, dados):
        self.tipo = tipo
        self.id = random.randint(0, 1000)
        self.origem = origem # IP da origem do pedido
        self.dados = dados
        self.datetime = datetime.datetime.now()

    def get_id(self):
        return self.id
    
    def get_origem(self):
        return self.origem
    
    def get_dados(self):
        return self.dados

    def serialize(self):
        return pickle.dumps(self)
    
    @staticmethod
    def deserialize(bytes):
        return pickle.loads(bytes)

    
    def __str__(self):
        return f"Message: {self.tipo}\nId: {self.id}\nOrigem: {self.origem}\nDados: {self.dados}"
    
    def __repr__(self):
        return self.__str__()

