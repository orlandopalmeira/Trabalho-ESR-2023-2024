import threading

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):
        self.videos = {} # conjunto de ids de videos
        self.videoslock = threading.Lock()
        self.vizinhos = dict()
        self.vizinhoslock = threading.Lock()

    def add_vizinho(self, ip, port):
        self.vizinhoslock.acquire()
        self.vizinhos[ip] = port
        self.vizinhoslock.release()

    def remove_vizinho(self, ip):
        self.vizinhoslock.acquire()
        self.vizinhos.pop(ip)
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
        self.videoslock.acquire()
        self.videos.remove(video_id)
        self.videoslock.release()

