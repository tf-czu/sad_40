"""
    TODO
"""

from osgar.node import Node
from osgar.bus import BusShutdownException
import datetime
import os.path
import numpy as np
import cv2


class MeasureNode(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('work_dir', "arecont_prev", "basler_prev", "rs_prev", "depth_prev", "route_prev")
        self.control_msg = None
        self.bus = bus
        self.storage_path = config.get("storage_path", "/home/ovosad/ovosad_data")
        self.wdn1 = datetime.datetime.now().strftime("%y%m%d") # day working dir

    def make_dir(self, label):
        wdn2 = f"{datetime.datetime.now().strftime('%H%M%S')}_{label}"
        work_dir_name = os.path.join(self.storage_path, self.wdn1, wdn2)
        os.makedirs(work_dir_name)

        return work_dir_name

    def process_image(self, image_data):
        if not isinstance(image_data, np.ndarray):
            image_data = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), 1)  # numpy arr from basler and rs?
        resized = cv2.resize(image_data, (600, 450))
        __, ret_im = cv2.imencode('*.jpeg', resized)

        return ret_im

    def process_depth(self, depth):
        depth_color = cv2.applyColorMap(cv2.convertScaleAbs(depth, alpha=0.03), cv2.COLORMAP_JET)
        resized = cv2.resize(depth_color, (600, 450))
        __, ret_im = cv2.imencode('*.jpeg', resized)

        return ret_im

    def on_control_msg(self, data):
        work_dir_name = self.make_dir(data)
        self.publish("work_dir", work_dir_name)

    def on_arecont_image(self, data):
        self.publish("arecont_prev", self.process_image(data))

    def on_basler_image(self, data):
        self.publish("basler_prev", self.process_image(data))

    def on_rs_image(self, data):
        self.publish("rs_prev", self.process_image(data))

    def on_rs_depth(self, data):
        self.publish("depth_prev", self.process_depth(data))

    def on_route_image(self, data):
        self.publish("route_prev", self.process_image(data))
