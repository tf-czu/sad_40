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
        self.verbose = False

    def on_image(self, data):
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), 1)
        qr_data = decode(frame)
        if self.verbose:
            print(qr_data, frame.shape)
        if qr_data:
            self.publish("qr_data", qr_data)
