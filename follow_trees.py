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
        bus.register("desired_speed")
        self.bus = bus
        self.verbose = False

    def scan_transform(self, scan):
        scan = np.array(scan)
        ret_scan = np.zeros_like(scan)
        ret_scan[:405] = scan[270:675]
        return ret_scan

    def on_scan(self, data):
        scan = self.scan_transform(data)
        desired_direction = normalizeAnglePIPI(follow_wall_angle(scan, gap_size=3, wall_dist=1, right_wall=True))
        print(math.degrees(desired_direction))

