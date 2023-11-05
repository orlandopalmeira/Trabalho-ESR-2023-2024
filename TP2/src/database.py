import threading
import json
import datetime

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):

        self.streaming = dict() # {nome_video: [addr]}
        self.streamingLock = threading.Lock()

        self.vizinhos = set()
        self.vizinhoslock = threading.Lock()

        #? Talvez se possa fazer um dict: ip destino -> [ip vizinho] em que a ordem é a de preferencia
        self.routingTable = dict() # ip destino -> ip vizinho
        self.routingTableLock = threading.Lock()

        self.pedidosRespondidos = list() # lista de (id, timestamp) de pedidos respondidos. A timestamp existe para que se possa remover da lista passado um certo tempo
        self.pedidosRespondidosLock = threading.Lock()


    # Lê o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath):
        with open(filepath) as f:
            data = json.load(f)
        with self.vizinhoslock:
            self.vizinhos = set(data["vizinhos"])

    def add_vizinho(self, ip):
        with self.vizinhoslock:
            self.vizinhos.add(ip)

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
    
    def get_vizinhos_for_broadcast(self, exclude_address):
        with self.vizinhoslock:
            return [v for v in self.vizinhos if v != exclude_address]

    def quantos_vizinhos(self):
        with self.vizinhoslock:
            quantos = len(self.vizinhos)
        return quantos

    def is_streaming_video(self, video):
        with self.streamingLock:
            return video in self.streaming
        
    def get_clients_streaming(self, video):
        with self.streamingLock:
            if video not in self.streaming:
                return []
            tuples = self.streaming[video].copy()
        # return list(map(lambda x: x[1], tuples))
        return tuples
            
    def add_streaming(self, video, addr):
        with self.streamingLock:
            if video in self.streaming:
                self.streaming[video].append(addr)
            else:
                self.streaming[video] = [addr]

    def remove_streaming(self, video, addr):
        with self.streamingLock:
            try:
                self.streaming[video] = [x for x in self.streaming[video] if x != addr] #> Remove o endereço addr da lista, se existir
                if len(self.streaming[video]) == 0:
                    del self.streaming[video]
                print("Streaming removido com sucesso")
            except KeyError:
                print("Streaming não existia")

    def add_route(self, ip_destino:str, ip_vizinho:str):
        with self.routingTableLock:
            self.routingTable[ip_destino] = ip_vizinho

    #? Método inutilizado uma vez que a remoção da rota ja é feita automaticamente na remove_streaming
    def remove_route(self, ip_destino:str):
        with self.routingTableLock:
            try:
                del self.routingTable[ip_destino]
                return "Rota removida com sucesso"
            except KeyError:
                return "Rota não existia"
            
    def resolve_ip_to_vizinho(self, ip_destino:str):
        with self.routingTableLock:
            return self.routingTable[ip_destino] #! TALVEZ Especificar melhor o que acontece quando n é encontrado o ip destino, apesar de ser praticamente impossivel
            
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
        




    def __str__(self):
        with self.vizinhoslock:
            with self.routingTableLock:
                with self.pedidosRespondidosLock:
                    with self.streamingLock:
                        return f"Database:\n\tvizinhos: {self.vizinhos}\n\troutingTable: {self.routingTable}\n\tpedidosRespondidos: {self.pedidosRespondidos}\n\tstreaming: {self.streaming}"

    def __repr__(self):
        return self.__str__()

