"""
    TODO
"""
import math
import numpy as np

from osgar.node import Node
from osgar.explore import follow_wall_angle
from osgar.lib.mathex import normalizeAnglePIPI


class FollowTrees(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register("desired_speed", "scan")
        self.bus = bus
        self.max_speed = config.get("max_speed", 0.5)
        self.scan = None

    def scan_transform(self, scan):  # rotate lidar by 90 deg, it could be removed in the future
        scan = np.array(scan)
        ret_scan = np.zeros_like(scan)
        ret_scan[:405] = scan[270:675]
        return ret_scan

    def send_speed(self, speed, desired_direction):
        return self.publish('desired_speed', [round(speed * 1000), round(math.degrees(desired_direction) * 100)])

    def go_safely(self, desired_direction):
        # TODO stop if a obstacle is too close.
        self.send_speed(self.max_speed, desired_direction)

    def on_scan(self, data):
        self.scan = self.scan_transform(data)
        desired_direction = normalizeAnglePIPI(follow_wall_angle(self.scan, gap_size=3, wall_dist=1, right_wall=True))
        self.publish("scan", self.scan)
        self.go_safely(desired_direction)

