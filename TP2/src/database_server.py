import threading
import json
import datetime

class Database_Server:

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videosLock = threading.Lock()

        self.streamsLock = threading.Lock()
        self.streams = dict() # {nome_video: Servidor}

        self.rp_addr_Lock = threading.Lock()
        self.rp_addr = None # string

    # Lê o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath):
        with open(filepath) as f:
            data = json.load(f)
        if "videos" in data:
            with self.videosLock:
                self.videos = set(data["videos"])
        else:
            print("AVISO: Não existem videos no ficheiro de configuração!!!")
        with self.rp_addr_Lock:
            self.rp_addr = data["rp_addr"]


    def add_video(self, video):
        with self.videosLock:
            self.videos.add(video)

    def remove_video(self, video):
        with self.videosLock:
            try:
                self.videos.remove(video)
                return "Vídeo removido com sucesso"
            except KeyError:
                return "Video não existia"
            
    def has_video(self, video):
        with self.videosLock:
            return video in self.videos
        
    def get_videos(self):
        with self.videosLock:
            return self.videos.copy()
            
    def add_stream(self, video, event, addr):
        with self.streamsLock:
            self.streams[video].append((event, addr))

    def remove_stream(self, video):
        with self.streamsLock:
            try:
                del self.streams[video]
                return "Streaming removido com sucesso"
            except KeyError:
                return "Streaming não existia"
            
    def is_rp_addr(self, addr):
        with self.rp_addr_Lock:
            return addr == self.rp_addr