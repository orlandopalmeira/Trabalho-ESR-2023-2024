import threading
import json
from Databases.database import Database

class Database_RP(Database):

    def __init__(self):
        super().__init__()

        self.serverInfo = dict() # ip-fonte: {"metric": metric:int, "contents": contents:list_of_videos}
        self.serverInfoLock = threading.Lock()

    def read_config_file(self, filepath):
        super().read_config_file(filepath)
        with open(filepath) as f:
            data = json.load(f)
        servs = data["servidores"]
        with self.serverInfoLock:
            for s in servs:
                self.serverInfo[s] = {"metric": 0, "contents": []}

    def get_best_server(self, movie_name) -> str:
        """Retorna o ip do melhor servidor para o filme movie_name"""
        with self.serverInfoLock:
            best = None
            for serv in self.serverInfo:
                if movie_name in self.serverInfo[serv]["contents"]:
                    if best == None or self.serverInfo[serv]["metric"] > self.serverInfo[best]["metric"]:
                        best = serv
        return best
    
    def servers_have_video(self, movie_name) -> bool:
        """Retorna True se algum servidor tiver o filme movie_name"""
        with self.serverInfoLock:
            for serv in self.serverInfo:
                if movie_name in self.serverInfo[serv]["contents"]:
                    return True
        return False

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



    def __str__(self):
        s = super().__str__()
        s += "\nServer Info:\n"
        with self.serverInfoLock:
            for serv in self.serverInfo:
                s += f"\t{serv}:\n"
                for key in self.serverInfo[serv]:
                    s += f"\t\t{key}: {self.serverInfo[serv][key]}\n"
        return s
        
    def __repr__(self):
        return self.__str__()