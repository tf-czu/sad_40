"""
    TODO
"""
import math

from osgar.node import Node
from osgar.explore import follow_wall_angle
from osgar.lib.mathex import normalizeAnglePIPI


class FollowTrees(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register("move")
        self.bus = bus
        self.max_speed = config.get("max_speed", 0.3)
        self.scan = None

    def send_speed(self, speed, desired_direction):
        # reverse direction
        return self.publish('move', [round(-speed * 1000), round(math.degrees(-desired_direction) * 100)])

    def go_safely(self, desired_direction):
        # TODO stop if a obstacle is too close.
        self.send_speed(self.max_speed, desired_direction)

    def on_scan(self, data):
        self.scan = data
        desired_direction = normalizeAnglePIPI(follow_wall_angle(self.scan, gap_size=3, wall_dist=1.5, right_wall=True))
        if desired_direction is not None:
            self.go_safely(desired_direction)
        else:
            self.send_speed(0, 0)

