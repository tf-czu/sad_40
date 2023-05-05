"""
    Simple zmq transmitter and receiver
"""

import zmq
import contextlib
import osgar.lib.serialize


class ZmqPull:
    def __init__(self, endpoint = "tcp://192.168.1.10:5555"): # "tcp://127.0.0.1:5555"
        self.endpoint = endpoint
        self.clear_images()

    def clear_images(self):
        self.basler_prev = None
        self.arecont_prev = None
        self.rs_prev = None
        self.depth_prev = None
        self.route_prev = None


    def pull_msg(self):
        context = zmq.Context.instance()
        socket = context.socket(zmq.PULL)
        # https://stackoverflow.com/questions/7538988/zeromq-how-to-prevent-infinite-wait
        socket.RCVTIMEO = 200  # milliseconds

        socket.connect(self.endpoint)
        with contextlib.closing(socket):
            while True:
                try:
                    channel, raw = socket.recv_multipart()
                    channel = channel.decode('ascii')
                    data = osgar.lib.serialize.deserialize(raw)
                    setattr(self, channel, data)

                except zmq.error.Again:
                        pass


def push_msg(data, endpoint = "tcp://192.168.1.10:5556"):  # "tcp://127.0.0.1:5556"
    context = zmq.Context.instance()
    socket = context.socket(zmq.PUSH)

    # https://stackoverflow.com/questions/7538988/zeromq-how-to-prevent-infinite-wait
    socket.SNDTIMEO = int(1000)  # convert to milliseconds
    socket.LINGER = 100  # milliseconds
    socket.connect(endpoint)

    try:
        with contextlib.closing(socket):
            raw = osgar.lib.serialize.serialize(data)
            socket.send_multipart([bytes("control_msg", 'ascii'), raw])
    except zmq.ZMQError as e:
        print(e)
