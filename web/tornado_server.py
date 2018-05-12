import numpy as np
import io
import scipy.io.wavfile

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

    def on_message(self, message):
        s = io.BytesIO(message)
        _, samplesints = scipy.io.wavfile.read(s)
        samples = samplesints.astype(np.float32, order='C') / 32768.0
        for i in range(0, len(samples) // buffer_size - 1):
            self.in_queue.put(samples[i * buffer_size:(i + 1) * buffer_size])

    def on_close(self):
        self.accompanist.stop()

    def send_audio(self, message):
        output = io.BytesIO()
        scipy.io.wavfile.write(output, 44100, message)
        self.write_message(output.getvalue(), binary=True)


def main():
    app = tornado.web.Application([url(r"/ws", WebSocketHandler)])
    return app


if __name__ == "__main__":
    app = main()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8070, address='127.0.0.1')
    ioloop.IOLoop.instance().start()
