"""
    TODO
"""
import os.path

from osgar.node import Node
from osgar.bus import BusShutdownException
import datetime


class MeasureNode(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('work_dir')
        self.control_msg = None
        self.bus = bus
        self.storage_path = config.get("storage_path", "/home/ovosad/ovosad_data")
        self.wdn1 = datetime.datetime.now().strftime("%y%m%d") # day working dir

    def make_dir(self, label):
        wdn2 = f"{datetime.datetime.now().strftime('%H%M%S')}_{label}"
        work_dir_name = os.path.join(self.storage_path, self.wdn1, wdn2)
        os.makedirs(work_dir_name)

        return work_dir_name


    def run(self):
        try:
            while self.is_bus_alive():
                self.update()
                if self.control_msg is not None:
                    work_dir_name = self.make_dir(self.control_msg)
                    self.publish("work_dir", work_dir_name)
                    self.control_msg = None

        except BusShutdownException:
            pass
