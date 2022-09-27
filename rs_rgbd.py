"""
    TODO
"""

import pyrealsense2 as rs
from osgar.node import Node
import numpy as np
import os
import cv2


class Realsense_cam(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('depth', 'color')
        self.bus = bus
        self.work_dir = None

        ctx = rs.context()
        self.pipeline = rs.pipeline(ctx)
        self.depth_cfg = rs.config()
        self.depth_cfg.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 5)
        self.depth_cfg.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 5)


    def save_frames(self, frames):
        depth, color = frames
        np.save(os.path.join(self.work_dir, "rs_depth"), depth)
        cv2.imwrite(os.path.join(self.work_dir, "rs_rgb.png"), color)


    def rs_take_pic(self):
        self.pipeline.start(self.depth_cfg)
        for ii in range(10):
            self.pipeline.wait_for_frames()

        frameset = self.pipeline.wait_for_frames()
        depth_frame = frameset.as_frameset().get_depth_frame()
        depth_image = np.asanyarray(depth_frame.as_depth_frame().get_data())

        color_frame = frameset.as_frameset().get_color_frame()
        color_image = np.asanyarray(color_frame.as_video_frame().get_data())

        self.pipeline.stop()

        return depth_image, color_image


    def update(self):
        timestamp, channel, data = self.listen()
        if channel == "work_dir":
            self.work_dir = data
            frames = self.rs_take_pic()
            if frames:
                self.publish("depth", frames[0])
                self.publish("color", frames[1])
                self.save_frames(frames)
