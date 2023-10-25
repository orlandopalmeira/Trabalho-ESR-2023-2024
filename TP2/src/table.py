import threading

class Table:
    # shared_variable = 0  # This is a class variable

    def __init__(self):
        self.lock = threading.Lock()
        self.videos = {} # conjunto de ids de videos

    def add_video(self, video_id):
        self.lock.acquire()
        self.videos.add(video_id)
        self.lock.release()

    def remove_video(self, video_id):
        self.lock.acquire()
        self.videos.remove(video_id)
        self.lock.release()

