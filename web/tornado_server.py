import numpy as np
import io
from pydub import AudioSegment

import tornado.websocket
from tornado import ioloop
from tornado.web import url

from production import accompanist
from multiprocessing import Queue

buffer_size = 256


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def initialize(self):
        self.in_queue = Queue()
        self.accompanist = None

    def open(self):
        self.accompanist = accompanist.Accompanist(self)
        self.accompanist.set_queue_in(self.in_queue)
        self.accompanist.run()

        print("Connected to tornado server")
        self.write_message("Connected to tornado server")

    def on_message(self, message):
        print("Chunk received")
        s = io.BytesIO(message)
        sound = AudioSegment.from_file(s, 'wav')
        samples = np.fromstring(sound.raw_data, dtype=np.float32)
        for i in range(0, len(samples) // buffer_size - 1):
            self.in_queue.put(samples[i * buffer_size:(i + 1) * buffer_size])

        self.write_message("Chunk received")

    def on_close(self):
        self.accompanist.stop()

    def send_audio(self, message):
        self.write_message("Chunk sent")
        self.write_message(message, binary=True)


def main():
    app = tornado.web.Application([url(r"/ws", WebSocketHandler)])
    return app


if __name__ == "__main__":
    app = main()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8070, address='127.0.0.1')
    ioloop.IOLoop.instance().start()
