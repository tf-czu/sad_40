"""
    TODO
"""
import math

from osgar.node import Node
from osgar.explore import follow_wall_angle
from osgar.lib.mathex import normalizeAnglePIPI
from subt.local_planner import LocalPlanner


class FollowTrees(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register("move")
        self.bus = bus
        self.max_speed = config.get("max_speed", 0.3)
        use_local_planner = config.get("local_planner", True)
        self.scan = None
        if use_local_planner:
            self.local_planner = LocalPlanner(scan_subsample=3)
        else:
            self.local_planner = None

    def send_speed(self, speed, desired_direction):
        # reverse direction
        return self.publish('move', [round(-speed * 1000), round(math.degrees(-desired_direction) * 100)])

    def go_safely(self, desired_direction):
        # TODO stop if a obstacle is too close.
        self.send_speed(self.max_speed, desired_direction)

    def on_scan(self, data):
        data[-30:] = [0]*30
        self.scan = data
        self.local_planner.update(data)
        desired_direction = normalizeAnglePIPI(follow_wall_angle(self.scan, gap_size=4, wall_dist=1.5, right_wall=True))
        if desired_direction is not None:
            # print(self.time, desired_direction, "\n")
            if self.local_planner:
                safety, desired_direction = self.local_planner.recommend(desired_direction)
            # print("planer", safe_direction)
            self.go_safely(desired_direction)
        else:
            self.send_speed(0, 0)

