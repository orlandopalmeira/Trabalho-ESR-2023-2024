import random


class Message:
    def __init__(self, tipo:int, fromip:str, dados, lista:list, id=random.randint(0, 1000)):
        self.tipo = tipo
        self.id = id
        self.fromip = fromip
        self.dados = dados
        self.lista = lista

    def toBytes(self):
        return "bytes"
    
    def fromBytes(self, bytes):
        return "message"
