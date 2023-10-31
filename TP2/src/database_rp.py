import threading
import json
from database import Database

class Database_RP(Database):

    def __init__(self):
        super().__init__()

        self.serverInfoLock = threading.Lock()
        self.serverInfo = dict() # ip-fonte: {"metric": metric:int, "contents": contents:list_of_videos}

    def read_config_file(self, filepath):
        super().read_config_file(filepath)
        with open(filepath) as f:
            data = json.load(f)
        servs = data["servidores"]
        with self.serverInfoLock:
            for s in servs:
                self.serverInfo[s] = dict()

    def get_best_server(self, movie_name):
        """Retorna o melhor servidor para o filme movie_name"""
        with self.serverInfoLock:
            best = None
            for serv in self.serverInfo:
                if movie_name in self.serverInfo[serv]["contents"]:
                    if best == None or self.serverInfo[serv]["metric"] < self.serverInfo[best]["metric"]:
                        best = serv
        return best

    def get_servidores(self):
        """Retorna os ips dos servidores"""
        with self.serverInfoLock:
            r = list(self.serverInfo.keys()).copy()
            return r
        
    def remove_servidor(self, serv):
        with self.serverInfoLock:
            try:
                del self.serverInfo[serv]
                print( f"Servidor {serv} removido com sucesso")
                return f"Servidor {serv} removido com sucesso"
            except KeyError:
                print( f"Servidor {serv} não existia")
                return f"Servidor {serv} não existia"

    def atualiza_servidor(self, fonte, metric, contents):
        with self.serverInfoLock:
            self.serverInfo[fonte] = {"metric": metric, "contents": contents}

    def atualiza_metrica(self, fonte, metric):
        with self.serverInfoLock:
            self.serverInfo[fonte]["metric"] = metric

    def atualiza_contents(self, fonte, contents):
        with self.serverInfoLock:
            self.serverInfo[fonte]["contents"] = contents
