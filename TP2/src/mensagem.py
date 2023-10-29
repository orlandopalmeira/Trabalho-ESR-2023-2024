import random
import datetime
import pickle


class Mensagem:
    #! WIP
    start_video = 1 # Pede o vídeo e nos dados, vem o nome do vídeo
    metrica     = 2 # Pede a métrica
    stop_video  = 3 # Pede para parar o vídeo
    check_video = 4 # Pede para verificar se tem um vídeo, e nome do nome vem no vídeo
    resp_check_video = 5 # Resposta ao pedido de check_video


    def __init__(self, tipo:int, origem:str, dados):
        self.tipo = tipo
        self.id = random.randint(0, 1000)
        self.origem = origem # IP da origem do pedido
        self.dados = dados
        self.datetime = datetime.datetime.now()

    def get_id(self):
        return self.id
    
    def get_tipo(self):
        return self.tipo
    
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
        tipo_name = [k for k, v in vars(self.__class__).items() if v == self.tipo][0]
        return f"Message: {tipo_name}\nId: {self.id}\nOrigem: {self.origem}\nDados: {self.dados}"
    
    def __repr__(self):
        return self.__str__()

