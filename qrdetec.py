"""
    Simple QR code detector
"""
import cv2
import numpy as np
from pyzbar.pyzbar import decode

from osgar.node import Node

class QrDetec(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('qr_data')
        self.bus = bus
        self.counter = 0
        self.verbose = False

    def on_image(self, data):
        self.counter += 1
        if self.counter == 2:
            self.counter = 0
            frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), 1)
            qr_data = decode(frame)
            if self.verbose:
                print(qr_data, frame.shape)
            if qr_data:
                self.publish("qr_data", qr_data)
