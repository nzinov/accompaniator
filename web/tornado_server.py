import tornado.websocket
from tornado.web import url

from production import accompanist
from multiprocessing import Queue


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.in_queue = Queue()
        self.accompanist = None

    def open(self):
        self.accompanist = accompanist.Accompanist(self)
        self.accompanist.set_queue_in(self.in_queue)
        self.accompanist.run()

        self.write_message("Connected to tornado server")

    def on_message(self, message):
        self.in_queue.put_nowait(message)
        self.write_message("Chunk received")

    def on_close(self):
        self.accompanist.stop()

    def send_audio(self, message):
        self.write_message("Chunk sent")
        self.write_message(message, binary=True)

def main():
    app = tornado.web.Application([url(r"/websocket", WebSocketHandler)])
    return app

if __name__ == "__main__":
    app = main()
