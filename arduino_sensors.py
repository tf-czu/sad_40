"""
    TODO
"""
import os
from osgar.node import Node


class ArduinoSensors(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('trig')
        self.bus = bus
        self.work_dir = None
        self.buf = b""
        # switch arduino to trigger mode
        self.publish("trig", b"\r\n")

    def save_data(self, data):
        assert self.work_dir is not None
        with open(os.path.join(self.work_dir, "arduino_sensors.txt"), "w") as f:
            f.write(data)

    def on_work_dir(self, data):
        self.work_dir = data
        self.publish("trig", b"\r\n")
        self.sleep(1)

    def on_raw(self, data):
        if self.work_dir:
            self.buf += data
            if b"\n" in self.buf:
                self.save_data(self.buf.decode())
                self.work_dir = None
                self.buf = b""
