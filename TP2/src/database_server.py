import threading
import json
import datetime

class Database_Server:

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videoslock = threading.Lock()

        self.streamsLock = threading.Lock()
        self.streams = dict() # {nome_video: [(thread.event, addr)]}

    # Lê o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath):
        with open(filepath) as f:
            data = json.load(f)
        with self.videoslock:
            self.videos = set(data["videos"])

    def add_video(self, video):
        self.videoslock.acquire()
        self.videos.add(video)
        self.videoslock.release()

    def remove_video(self, video):
        with self.videoslock:
            try:
                self.videos.remove(video)
                return "Vídeo removido com sucesso"
            except KeyError:
                return "Video não existia"
            
    def has_video(self, video):
        with self.videoslock:
            return video in self.videos
        
    def get_videos(self):
        with self.videoslock:
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