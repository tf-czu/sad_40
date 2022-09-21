"""
   Osgar driver for Basler camera.
"""

import cv2
from threading import Thread
from pypylon import pylon


class BaslerCamera:
    def __init__(self, config, bus):
        self.input_thread = Thread(target=self.run_input, daemon=True)
        self.bus = bus
        self.bus.register('picture', 'metadata')
        self.address = config.get("address", False)

        tlf = pylon.TlFactory.GetInstance()
        if not self.address:
            self.cam = pylon.InstantCamera(tlf.CreateFirstDevice())
        else:
            self.cam = None
            for dev_info in tlf.EnumerateDevices():
                if dev_info.GetDeviceClass() == 'BaslerGigE':
                    if dev_info.GetIpAddress() == self.address:
                        self.cam = pylon.InstantCamera(tlf.CreateDevice(dev_info))
                        break
            else:
                raise EnvironmentError("no GigE device found")

        self.cam.Open()

        self.cam.ExposureAuto.SetValue('Continuous')
        # self.cam.ExposureTimeAbs.SetValue(170_000)
        # self.cam.GainAuto.SetValue("Off")
        # self.cam.GainRaw.SetValue(34)

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def start(self):
        self.input_thread.start()

    def join(self, timeout=None):
        self.input_thread.join(timeout=timeout)

    def run_input(self):
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while self.bus.is_alive():
            assert self.cam.IsGrabbing()
            try:
                result = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if result.GrabSucceeded():
                    image = self.converter.Convert(result)
                    picture = image.GetArray()
                    retval, data = cv2.imencode('*.png', picture)
                    if len(data) > 0:
                        self.bus.publish('picture', data.tobytes())
            except Exception as e:
                print(e)

    def request_stop(self):
        self.cam.StopGrabbing()
        self.cam.Close()
        self.bus.shutdown()
