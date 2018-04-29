import tornado.websocket
from production import accompanist

from multiprocessing import Queue

class WSHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.in_queue = Queue()
        self.accompanist = None

    def open(self):
        self.accompanist = accompanist.Accompanist(self)
        self.accompanist.set_queue_in(self.in_queue)
        self.accompanist.run()

        self.write_message("Connected to tornado server")

    def on_message(self, message):
        # Check if message is Binary or Text
        self.in_queue.put_nowait(message)
        self.write_message("Chunk received")

    def on_close(self):
        self.accompanist.stop()

    def send_audio(self, message):
        self.write_message("Chunk sent")
        self.write_message(message, binary=True)
