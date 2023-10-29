import threading
from database import Database

class Database_RP(Database):

    def __init__(self):
        super().__init__()

        self.metricTableLock = threading.Lock()
        self.metricTable = dict() # ip-fonte: {"metric": metric:int, "contents": contents:list_of_videos}

    def adiciona_fonte(self, fonte, metric, contents):
        with self.metricTableLock:
            self.metricTable[fonte] = {"metric": metric, "contents": contents}

    def altera_metrica(self, fonte, metric):
        with self.metricTableLock:
            self.metricTable[fonte]["metric"] = metric

    def altera_contents(self, fonte, contents):
        with self.metricTableLock:
            self.metricTable[fonte]["contents"] = contents
