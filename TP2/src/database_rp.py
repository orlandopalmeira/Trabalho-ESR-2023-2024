import threading
import json
from database import Database

class Database_RP(Database):

    def __init__(self):
        super().__init__()

        self.metricTableLock = threading.Lock()
        self.metricTable = dict() # ip-fonte: {"metric": metric:int, "contents": contents:list_of_videos}

    def read_config_file(self, filepath):
        super().read_config_file(filepath)
        with open(filepath) as f:
            data = json.load(f)
        servs = data["servidores"]
        with self.metricTableLock:
            for s in servs:
                self.metricTable[s] = dict()

    def get_servidores(self):
        """Retorna os ips dos servidores"""
        with self.metricTableLock:
            return self.metricTable.keys().copy()
        
    def remove_servidor(self, serv):
        with self.metricTableLock:
            try:
                del self.metricTable[serv]
                print( f"Servidor {serv} removido com sucesso")
                return f"Servidor {serv} removido com sucesso"
            except KeyError:
                print( f"Servidor {serv} não existia")
                return f"Servidor {serv} não existia"


    def adiciona_fonte(self, fonte, metric, contents):
        with self.metricTableLock:
            self.metricTable[fonte] = {"metric": metric, "contents": contents}

    def altera_metrica(self, fonte, metric):
        with self.metricTableLock:
            self.metricTable[fonte]["metric"] = metric

    def altera_contents(self, fonte, contents):
        with self.metricTableLock:
            self.metricTable[fonte]["contents"] = contents
