import cv2
from threading import Thread
from queue import Queue

class Camera:
    def __init__(self, index=0, queue_size=2, width=640, height=480):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
        self.q = Queue(maxsize=queue_size)
        self.running = False

    def start(self):
        if not self.cap.isOpened():
            raise RuntimeError("❌ Cannot open camera.")
        self.running = True
        Thread(target=self._loop, daemon=True).start()
        return self

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                continue
            if self.q.full():
                self.q.get()
            self.q.put(frame)

    def read(self):
        return None if self.q.empty() else self.q.get()

    def stop(self):
        self.running = False
        self.cap.release()
