import threading
import json

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videoslock = threading.Lock()
        self.vizinhos = set()
        self.vizinhoslock = threading.Lock()

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

    # Printa os vizinhos
    def show_vizinhos(self):
        self.vizinhoslock.acquire()
        print()
        print(f"Vizinhos: {self.vizinhos}")
        print(f"Quantidade: {len(self.vizinhos)}")
        print()
        self.vizinhoslock.release()
    
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

