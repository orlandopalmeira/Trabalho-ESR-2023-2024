import threading
import json
import os
import sys


class Database_Server:

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videosLock = threading.Lock()

        self.streams = dict() # {nome_video: ServerWorker}
        self.streamsLock = threading.Lock()

        self.videos_dir = "./videos/" # Valor Default


    # Lê o ficheiro de configuração JSON e guarda o necessário na base de dados
    def read_config_file(self, filepath):
        with open(filepath) as f:
            data = json.load(f)
        if "videos" in data:
            with self.videosLock:
                self.videos = set(data["videos"])
        else:
            print("AVISO: Não existem videos no ficheiro de configuração!!!")
        if "videos_dir" in data:
            self.videos_dir = data["videos_dir"]
        if self.videos_dir[-1] != "/":
            self.videos_dir += "/"
        if not os.path.exists(self.videos_dir):
            print(f"Diretoria de videos fornecida {self.videos_dir} não existe!!")
            sys.exit(1)
        print(f"Diretoria dos vídeos definida: {self.videos_dir}")

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
            
    def add_stream(self, video, serverWorker):
        with self.streamsLock:
            self.streams[video] = serverWorker

    def remove_stream(self, video):
        with self.streamsLock:
            try:
                self.streams[video].stop_serving() # faz com que o work que está a emitir o vídeo termine
                del self.streams[video] # retira a stream da base de dados.
                return "Streaming removido com sucesso"
            except KeyError:
                print(self.streams)
                return "Streaming não existia"
    
    def is_streaming(self, video):
        with self.streamsLock:
            return video in self.streams.keys()


    def get_videos_dir(self):
        return self.videos_dir