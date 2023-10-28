import threading
import json
import datetime
import copy

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videoslock = threading.Lock()

        self.vizinhos = set()
        self.vizinhoslock = threading.Lock()

        # Talvez se possa fazer um dict: ip destino -> [ip vizinho] em que a ordem é a de preferencia
        self.routingTable = dict() # ip destino -> ip vizinho
        self.routingTableLock = threading.Lock()

        self.pedidosRespondidos = list() # lista de (id, timestamp) de pedidos respondidos. A timestamp existe para que se possa remover da lista passado um certo tempo
        self.pedidosRespondidosLock = threading.Lock()


    # L~e o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath):
        with open(filepath) as f:
            data = json.load(f)
            self.vizinhoslock.acquire()
            self.vizinhos = set(data["vizinhos"])
            self.vizinhoslock.release()

    def add_vizinho(self, ip):
        self.vizinhoslock.acquire()
        self.vizinhos.add(ip)
        self.vizinhoslock.release()

    def remove_vizinho(self, ip):
        with self.vizinhoslock:
            try:
                self.vizinhos.remove(ip)
                return "Vizinho removido com sucesso"
            except KeyError:
                return "Vizinho não existia"

    # Retorna uma copia dos vizinhos
    def get_vizinhos(self):
        with self.vizinhoslock:
            return self.vizinhos.copy()
    
    def quantos_vizinhos(self):
        self.vizinhoslock.acquire()
        quantos = len(self.vizinhos)
        self.vizinhoslock.release()
        return quantos

    def add_video(self, video_id):
        self.videoslock.acquire()
        self.videos.add(video_id)
        self.videoslock.release()

    def remove_video(self, video_id):
        with self.videoslock:
            try:
                self.videos.remove(video_id)
                return "Vídeo removido com sucesso"
            except KeyError:
                return "Video não existia"
            
    def add_route(self, ip_destino:str, ip_vizinho:str):
        with self.routingTableLock:
            self.routingTable[ip_destino] = ip_vizinho

    def remove_route(self, ip_destino:str):
        with self.routingTableLock:
            try:
                del self.routingTable[ip_destino]
                return "Rota removida com sucesso"
            except KeyError:
                return "Rota não existia"
            
    def get_routing_table(self):
        with self.routingTableLock:
            return self.routingTable.copy()
            
    def add_pedido_respondido(self, id: int):
        with self.pedidosRespondidosLock:
            self.pedidosRespondidos.append((id, datetime.datetime.now()))

    def remove_pedido_respondido(self):
        """Elimina pedido respondido há mais de 10 segundos"""
        now = datetime.datetime.now()
        with self.pedidosRespondidosLock:
            for i in range(len(self.pedidosRespondidos)):
                if self.pedidosRespondidos[i][1] < now - datetime.timedelta(seconds=10):
                    del self.pedidosRespondidos[i]

    def foi_respondido(self, id:int):
        with self.pedidosRespondidosLock:
            for i in range(len(self.pedidosRespondidos)):
                if self.pedidosRespondidos[i][0] == id:
                    return True
            return False

