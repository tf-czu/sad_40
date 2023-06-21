"""
   Osgar driver for Basler camera.
"""

import cv2
import os
import json
from threading import Thread
from pypylon import pylon

from osgar.node import Node


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
        # self.cam.AutoFunctionProfile.SetValue("MinimizeExposureTime")

        # self.cam.ExposureTimeAbs.SetValue(170_000)
        self.cam.GainAuto.SetValue("Off")
        self.cam.GainRaw.SetValue(255)

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def start(self):
        self.input_thread.start()

    def join(self, timeout=None):
        self.input_thread.join(timeout=timeout)

    def run_input(self):
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while self.bus.is_alive() and self.cam.IsGrabbing():
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


class BaslerCameraOnce(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        self.address = config.get("address", False)
        self.auto_expo = config.get("auto_expo", True)
        exposure_time_abs = config.get("exposure_time_abs", 170_000)
        gain_raw = config.get("gain_raw", 34)
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

        self.cam.ExposureAuto.SetValue('Off')
        self.cam.ExposureTimeAbs.SetValue(exposure_time_abs)
        self.cam.GainAuto.SetValue("Off")
        self.cam.GainRaw.SetValue(gain_raw)


        self.bus.register('picture:null')
        self.bus.register('metadata')

        if self.auto_expo:
            self.expo_value = -1
            self.set_exposure()
        else:
            self.expo_value = exposure_time_abs

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


    def set_exposure(self):
        """ Wait till exposure is adapted - timeout is 20 seconds.
        """
        self.cam.Width.SetValue(2304)
        self.cam.OffsetX.SetValue(2304)
        self.cam.ExposureAuto.SetValue('Once')

        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        for k in range(20):
            self.sleep(1)
            new_expo = self.cam.ExposureTimeAbs.GetValue()
            if abs(new_expo - self.expo_value) < 50:
                break
            #print(k, new_expo)
            self.expo_value = new_expo


        self.cam.StopGrabbing()
        self.cam.OffsetX.SetValue(0)
        self.cam.Width.SetValue(2*2304)
        print(self.expo_value)
        #self.cam.ExposureTimeRaw.SetValue(int(expo_value))
        self.cam.ExposureAuto.SetValue('Off')


    def update(self):
        dt, channel, data = self.listen()
        # print(dt, channel, data)
        if channel != "work_dir":
            return
        # data = "/home/ovosad/ovosad_data/test_basler_02"
        save_path = data

        if self.auto_expo:
            self.set_exposure()
            ev_values = [1, 0.5, 0.25, 0.125, 2, 4, 8]
        else:
            ev_values = [1]

        metadata = {"pictures": {}}

        pic2publish = None
        for ii, ev in enumerate(ev_values):
            try:
                self.cam.ExposureTimeAbs.SetValue(self.expo_value * ev)
                short_name = "im_basler_EV{}.tiff".format(ii)
                long_name = os.path.join(save_path, short_name)
                picture = self.take_pic(long_name)
                if picture is not None and ev == 1:
                    pic2publish = picture

                metadata["pictures"][short_name] = {
                    "path": str(long_name),
                    "exposure": self.cam.ExposureTimeAbs.GetValue(),
                }
            except Exception as e:
                pass
                print(e)
                try:
                    self.cam.StopGrabbing()
                except:
                    pass

        self.bus.publish("metadata", json.dumps(metadata))
        self.bus.publish("picture", pic2publish)

        meta_path = os.path.join(save_path, "basler_meta.json")
        with open(meta_path, "w") as f:
            f.write(json.dumps(metadata, indent=4))

    def take_pic(self, savepath):
        picture = None
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        try:
            result = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if result.GrabSucceeded():
                image = self.converter.Convert(result)
                picture = image.GetArray()
                cv2.imwrite(savepath, picture)

        except Exception as e:
            print(e)

        self.cam.StopGrabbing()

        return picture


    def request_stop(self):
        self.cam.StopGrabbing()
        self.cam.Close()
        self.bus.shutdown()
