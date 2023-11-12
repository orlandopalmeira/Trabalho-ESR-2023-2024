import threading
import json
import datetime

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):

        # Info acerca dos nós para os quais estou a fazer streaming
        self.streaming = dict() # {nome_video: [addr]} em que addr é um tuple (ip, port)
        self.streamingLock = threading.Lock()

        # Info acerca dos nós que me estão a transmitir streaming
        self.streaming_from = dict() # {ip: [nome_video]} em que ip é uma string
        self.streaming_fromLock = threading.Lock()

        # Info acerca dos meus vizinhos
        self.vizinhos = set()
        self.vizinhoslock = threading.Lock()

        #? Talvez se possa fazer um dict: ip destino -> [ip vizinho] em que a ordem é a de preferencia. 
        #* R: Acho que nem vai ser possivel com o bloqueio dos pedidos ja respondidos
        self.routingTable = dict() # ip destino -> ip vizinho
        self.routingTableLock = threading.Lock()

        # Lista de {id:int, origin:str, ts:timestamp) de pedidos respondidos. A timestamp existe para que se possa remover da lista passado um certo tempo
        self.pedidosRespondidos = list() 
        self.pedidosRespondidosLock = threading.Lock()


    # Lê o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath:str):
        with open(filepath) as f:
            data = json.load(f)
        with self.vizinhoslock:
            self.vizinhos = set(data["vizinhos"])

    def add_vizinho(self, ip:str):
        with self.vizinhoslock:
            self.vizinhos.add(ip)

    def remove_vizinho(self, ip:str):
        """Retorna 0 se o ip foi removido com sucesso, 1 caso não existisse"""
        r = 0
        with self.vizinhoslock:
            try:
                self.vizinhos.remove(ip)
            except KeyError:
                r = 1
        self.remove_streaming_for_ip(ip)
        self.remove_ip_streaming_from(ip)
        self.remove_route_for_ip(ip)
        return r

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

    def is_streaming_video(self, video:str):
        with self.streamingLock:
            return video in self.streaming
        
    def get_clients_streaming(self, video:str):
        with self.streamingLock:
            if video not in self.streaming:
                return []
            tuples = self.streaming[video].copy()
        # return list(map(lambda x: x[1], tuples))
        return tuples
            
    def add_streaming(self, video:str, addr:tuple):
        """Adiciona o endereço 'addr' à lista de endereços a enviar o streaming do video 'video'"""
        with self.streamingLock:
            if video in self.streaming:
                self.streaming[video].append(addr)
            else:
                self.streaming[video] = [addr]

    def remove_streaming(self, video:str, addr:tuple):
        with self.streamingLock:
            try:
                self.streaming[video] = [x for x in self.streaming[video] if x != addr] #> Remove o endereço addr da lista, se existir
                if len(self.streaming[video]) == 0:
                    del self.streaming[video]
                print("Streaming removido com sucesso")
            except KeyError:
                print("Streaming não existia")

    def remove_streaming_for_ip(self, ip:str):
        with self.streamingLock:
            for video in self.streaming:
                self.streaming[video] = [x for x in self.streaming[video] if x[0] != ip]
                if len(self.streaming[video]) == 0:
                    del self.streaming[video]

#####################? Merece revisão
#! Aplicar o add_streaming_from e remove_streaming_from em conjunto com o add_streaming e remove_streaming
    def add_streaming_from(self, ip_fornecedor:str, video:str):
        """Adiciona o video 'video' à lista de videos que estou a receber do ip 'ip_fornecedor'"""
        with self.streaming_fromLock:
            if ip_fornecedor in self.streaming_from:
                self.streaming_from[ip_fornecedor].append(video)
            else:
                self.streaming_from[ip_fornecedor] = [video]

    def remove_streaming_from(self, ip:str, video:str):
        with self.streaming_fromLock:
            try:
                self.streaming_from[ip].remove(video)
                if len(self.streaming_from[ip]) == 0:
                    del self.streaming_from[ip]
                print(f"Streaming_from de {ip} do video '{video}' removido com sucesso")
            except KeyError:
                print(f"Streaming_from de {ip} do video '{video}'")

    def remove_ip_streaming_from(self, ip:str):
        with self.streaming_fromLock:
            try:
                del self.streaming_from[ip]
            except KeyError:
                pass

    # talvez passar como argumento o video 
    def is_transmitting_video(self, ip:str):
        with self.streaming_fromLock:
            return ip in self.streaming_from

#?###################

    def remove_route_for_ip(self, ip:str):
        with self.routingTableLock:
            for ip_destino in self.routingTable:
                if self.routingTable[ip_destino] == ip:
                    del self.routingTable[ip_destino]

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
            
    def resolve_ip_to_vizinho(self, ip_destino:str):
        with self.routingTableLock:
            return self.routingTable[ip_destino] #! TALVEZ Especificar melhor o que acontece quando n é encontrado o ip destino, apesar de ser praticamente impossivel
            
    def get_routing_table(self):
        with self.routingTableLock:
            return self.routingTable.copy()
        
#* Secção de pedidos respondidos
#           
    def add_pedido_respondido(self, id_: int, origin: str):
        with self.pedidosRespondidosLock:
            self.pedidosRespondidos.append(
                {
                    "id": id_,
                    "origin": origin,
                    "ts": datetime.datetime.now(),
                }
            )
    
    def add_pedido_respondido_msg(self, msg):
        with self.pedidosRespondidosLock:
            self.pedidosRespondidos.append(
                {
                    "id": msg.get_id(),
                    "origin": msg.get_origem(),
                    "ts": datetime.datetime.now(),
                }
            )

    def remove_pedidos_respondidos(self, max_age_secs:int = 10):
        """Elimina pedido respondidos há mais de 'max_age_secs' segundos"""
        now = datetime.datetime.now()
        min_timestamp = now - datetime.timedelta(seconds=max_age_secs)
        with self.pedidosRespondidosLock:
            self.pedidosRespondidos = list(filter(lambda p: p["ts"] > min_timestamp, self.pedidosRespondidos))

    def foi_respondido(self, _id:int, origin: str):
        with self.pedidosRespondidosLock:
            for p in self.pedidosRespondidos:
                if p["id"] == _id and p["origin"] == origin:
                    return True
            return False
    
    def foi_respondido_msg(self, msg):
        with self.pedidosRespondidosLock:
            for p in self.pedidosRespondidos:
                if p["id"] == msg.get_id() and p["origin"] == msg.get_origem():
                    return True
            return False
        




    def __str__(self):
        with self.vizinhoslock, self.routingTableLock, self.pedidosRespondidosLock, self.streamingLock:
            pedidosRespondidos_str = [
                {**pedido, 'ts': pedido['ts'].strftime('%Y-%m-%d %H:%M:%S')}
                for pedido in self.pedidosRespondidos.copy()
            ]
            return (
                f"\nDatabase:\n"
                f"\tstreaming: {self.streaming}\n"
                f"\tstreaming_from: {self.streaming_from}\n"
                f"\tvizinhos: {self.vizinhos}\n"
                f"\troutingTable: {self.routingTable}\n"
                f"\tpedidosRespondidos: {pedidosRespondidos_str}\n"
            )
    
    def __repr__(self):
        return self.__str__()

