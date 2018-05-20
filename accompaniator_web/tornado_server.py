# import sys
# sys.path.append("../")
import numpy as np
import io
import scipy.io.wavfile

import tornado.websocket
from tornado import ioloop
from tornado.web import url

from production import accompanist
from multiprocessing import Queue, Process

from datetime import datetime
import time

buffer_size = 256
time_between_delay_measurings_in_secs = 1.5


def send_time_stamps(websocket):
    while websocket.running is True:
        now = datetime.now()
        output = now.strftime("%Y-%m-%d %H:%M:%S")
        websocket.write_message(output, binary=False)
        time.sleep(time_between_delay_measurings_in_secs)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def initialize(self):
        self.in_queue = Queue()
        self.accompanist = None
        self.last_sent_time_stamp = None
        self.running = False

    def open(self):
        self.accompanist = accompanist.Accompanist()
        self.accompanist.set_websocket(self)
        self.accompanist.set_queue_in(self.in_queue)

        self.accompanist.run()

        self.running = True
        self.time_send_process = Process(target=send_time_stamps, args=(self,))
        self.time_send_process.start()

    def on_message(self, message):
        if 'RIFF' in str(message):
            s = io.BytesIO(message)
            _, samplesints = scipy.io.wavfile.read(s)
            samples = samplesints.astype(np.float32, order='C') / 32768.0
            for i in range(0, len(samples) // buffer_size - 1):
                self.in_queue.put(samples[i * buffer_size:(i + 1) * buffer_size])

        else:  # it's a time string!
            time_stamp = datetime.strptime(message, "%Y-%m-%d %H:%M:%S")
            delay = (datetime.now() - time_stamp).total_seconds()
            self.accompanist.set_web_delay(delay)

    def on_close(self):
        self.running = False
        self.time_send_process.join()
        self.accompanist.stop()

    def send_audio(self, message):
        print("delay ok!")
        output = io.BytesIO()
        scipy.io.wavfile.write(output, 44100, message)
        self.write_message(output.getvalue(), binary=True)

    def send_time(self):
        pass


def main():
    app = tornado.web.Application([url(r"/ws", WebSocketHandler)])
    return app


if __name__ == "__main__":
    app = main()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8110, address='0.0.0.0')
    ioloop.IOLoop.instance().start()
