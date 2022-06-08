"""
    TODO
"""

from osgar.node import Node
from osgar.bus import BusShutdownException
from datetime import timedelta

def make_dir(label):
    print(label)
    return "some_dir"  # TODO


class MeasureNode(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('workin_dir')
        self.control_msg = None
        self.bus = bus


    def run(self):
        try:
            while self.is_bus_alive():
                self.update()
                if self.control_msg is not None:
                    dir_name = make_dir(self.control_msg)
                    self.publish("workin_dir", dir_name)
                    self.control_msg = None

        except BusShutdownException:
            pass
