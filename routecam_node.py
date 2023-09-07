"""
    TODO
"""
import cv2
import os
from osgar.node import Node


class RouteCamNode(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('image')
        self.bus = bus
        self.work_dir = None

    def save_image(self, image):
        assert self.work_dir is not None, self.work_dir
        with open(os.path.join(self.work_dir, "route_im.jpg"), "wb") as f:
            f.write(image)

    def on_frame(self, data):
        if self.work_dir:
            frame = data
            retval, image_data = cv2.imencode('*.jpeg', frame)
            if len(image_data) > 0:
                self.bus.publish('image', image_data.tobytes())
                self.save_image(image_data)
                self.work_dir = None

    def on_work_dir(self, data):
        self.work_dir = data
