import random
import datetime
import pickle


class Mensagem:
    START_VIDEO = 1 # Pede o vídeo e nos dados, vem o nome do vídeo
    METRICA     = 2 # Pede a métrica
    STOP_VIDEO  = 3 # Pede para parar o vídeo
    CHECK_VIDEO = 4 # Pede para verificar se tem um vídeo, e nome do nome vem no vídeo
    RESP_CHECK_VIDEO = 5 # Resposta ao pedido de check_video
    ADD_VIZINHO = 6 # Notifica vizinhos da chegada de um novo vizinho
    RMV_VIZINHO = 7 # Notifica vizinhos da remoção de um novo vizinho
    ALIVE_RECEPTOR = 8 # Notifica fornecedor que ainda está vivo


    def __init__(self, tipo:int, dados="", origem:str = ""):
        self.tipo = tipo
        self.id:int = random.randint(0, 1000000)
        self.dados = dados
        self.origem:str = origem # IP da origem do pedido
        self.timestamp = None 

    def get_id(self):
        return self.id
    
    def get_tipo(self):
        return self.tipo
    
    def get_origem(self):
        return self.origem
    
    def get_dados(self):
        return self.dados
    
    def set_dados(self, dados):
        self.dados = dados
    
    def get_timestamp(self):
        return self.timestamp
    
    def update_timestamp(self):
        self.timestamp = datetime.datetime.now()

    def serialize(self):
        return pickle.dumps(self)
    
    @staticmethod
    def deserialize(bytes):
        return pickle.loads(bytes)

    
    def __str__(self):
        tipo_name = [k for k, v in vars(self.__class__).items() if v == self.tipo][0]
        # Retorna em formato de dicionário
        return f"{{\n\tTipo: {tipo_name},\n\tId: {self.id},\n\tOrigem: {self.origem},\n\tDados: {self.dados}\n}}"
    
    def __repr__(self):
        return self.__str__()

