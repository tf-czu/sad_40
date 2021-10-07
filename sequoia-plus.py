"""
    External osgar driver for Parrot Sequoia+ camera
    https://github.com/Parrot-Developers/sequoia-ptpy
"""

import ptpy

from threading import Thread

class LogSequoiaCamera:
    def __init__(self, config, bus):
        self.input_thread = Thread(target=self.run_input, daemon=True)
        self.bus = bus
        bus.register("event", "filename")
        self.camera = ptpy.PTPy()


    def start(self):
        self.input_thread.start()

    def join(self, timeout=None):
        self.input_thread.join(timeout=timeout)

    def run_input(self):
        with self.camera.session():
            capture = self.camera.initiate_open_capture()
            # start timelapse, parameters have to be set manually on the camera
            self.transactionID = capture.TransactionID
            while self.bus.is_alive():
                event = self.camera.event()
                if event:
                    self.bus.publish("event", event)
                    if event.EventCode == 'ObjectAdded':
                        handle = event.Parameter[0]
                        info = self.camera.get_object_info(handle)
                        if info.ObjectFormat != 'Association':
                            self.bus.publish("filename", info.Filename)


    def request_stop(self):
        with self.camera.session():
            self.camera.terminate_open_capture(self.transactionID)
        self.bus.shutdown()
