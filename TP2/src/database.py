import threading

class Database:
    # shared_variable = 0  # This is a class variable

    def __init__(self):
        self.videos = set() # conjunto de ids de videos
        self.videoslock = threading.Lock()
        self.vizinhos = set()
        self.vizinhoslock = threading.Lock()

    def add_vizinho(self, ip):
        self.vizinhoslock.acquire()
        self.vizinhos.add(ip)
        self.vizinhoslock.release()

    def remove_vizinho(self, ip):
        self.vizinhoslock.acquire()
        self.vizinhos.remove(ip)
        self.vizinhoslock.release()

    # Printa os vizinhos
    def show_vizinhos(self):
        self.vizinhoslock.acquire()
        print(f"Vizinhos: {self.vizinhos}")
        print(f"Quantidade: {len(self.vizinhos)}")
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

