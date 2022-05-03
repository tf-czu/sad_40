import os

from pypylon import pylon
import socket
import urllib.request
import pyrealsense2 as rs
import numpy as np
import datetime
import cv2 as cv
import json
import psutil
import time

HOST = "192.168.1.100"  # Basler camera
STORAGE_PATH = "/home/ovosad/ovosad_data"

ARECONT_URL = "http://192.168.1.36/img.jpg"
ARECONT_SET = "http://192.168.1.36/set?daynight=dual"


def get_disk_space():
    disk = psutil.disk_usage("/")
    return disk.free/1024**3


class Basler:
    def __init__(self, work_dir):
        self.address = HOST
        self.work_dir = work_dir
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
#        Set camera, move to separate method?
        self.cam.ExposureAuto.SetValue('Off')  # was "Continuous", "Once"
        self.cam.ExposureTimeAbs.SetValue(170_000)
#        self.cam.Gamma.SetValue(0.4)
        self.cam.GainAuto.SetValue("Off")
        self.cam.GainRaw.SetValue(34)
#        a = self.cam.Gain.GetValue()
        self.cam.AutoTargetValue.SetValue(85)
        self.cam.BalanceWhiteAuto.SetValue("Once")
#        self.cam.BlackLevelRaw.SetValue(500)

        settings_path = os.path.join(self.work_dir, "settings.pfs")
        pylon.FeaturePersistence.Save(settings_path, self.cam.GetNodeMap())

    def set_exposure(self):
        self.cam.Width.SetValue(2304)
        self.cam.OffsetX.SetValue(2304)
        self.cam.ExposureAuto.SetValue('Once')

        self.cam.StartGrabbing()
        time.sleep(0.2)
        self.cam.StopGrabbing()
        self.cam.ExposureAuto.SetValue('Off')

    def take_pic(self, file_path):
        self.set_exposure()
        self.cam.StartGrabbing()
        img = pylon.PylonImage()
        with self.cam.RetrieveResult(2000) as result:
            img.AttachGrabResultBuffer(result)
            img.Save(pylon.ImageFileFormat_Tiff, file_path)
            
            data = {
                    "exposure": self.cam.ExposureTimeAbs.GetValue(),
                    "gain": self.cam.GainRaw.GetValue(), 
                }

            img.Release()

        self.cam.StopGrabbing()
        
        return data


    def close_cam(self):
        self.cam.Close()

class Realsense_cam:
    def __init__(self):
        ctx = rs.context()
        self.pipeline = rs.pipeline(ctx)
        depth_cfg = rs.config()
        depth_cfg.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 5)
        depth_cfg.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 5)
        self.pipeline.start(depth_cfg)

    def rs_take_pic(self):
        frameset = self.pipeline.wait_for_frames()
        depth_frame = frameset.as_frameset().get_depth_frame()
        depth_image = np.asanyarray(depth_frame.as_depth_frame().get_data())

        color_frame = frameset.as_frameset().get_color_frame()
        color_image = np.asanyarray(color_frame.as_video_frame().get_data())

        return depth_image, color_image

    def rs_stop(self):
        self.pipeline.stop()


class Arecont:
    def __init__(self, url_set):
        try:
            with urllib.request.urlopen(url_set, timeout=0.5) as f:
                data = f.read()
            assert len(data) > 0
            print(data)
        except socket.timeout:
            pass

    def arecont_take_pic(self, url):
        try:
            # https://github.com/mesonbuild/meson/issues/4087
            # without timeout the call can hang the process forever
            with urllib.request.urlopen(url, timeout=0.5) as f:
                data = f.read()
            if len(data) > 0:
                return data
        except socket.timeout:
            pass


def main(label, note):
    day_name = datetime.datetime.now().strftime("%y%m%d")
    label_dir = "{}_{}".format(datetime.datetime.now().strftime("sad_%H%M%S"), label)
    # create working directory
    os.makedirs(os.path.join(STORAGE_PATH, day_name), exist_ok=True)
    work_dir_path = os.path.join(STORAGE_PATH, day_name, label_dir)
    os.makedirs(work_dir_path, exist_ok=True)

    basler = Basler(work_dir_path)
    rs_cam = Realsense_cam()
    set_url = ARECONT_SET
    url = ARECONT_URL
    arecont = Arecont(set_url)

    basler_data = {}
    if note is not None:
        basler_data["note"] = note
    pic_param_data = []
    print("scaning ..")
    for ii in range(5):
        arecont_img = arecont.arecont_take_pic(url)
        depth, rgb = rs_cam.rs_take_pic()
        basler_img_path = os.path.join(work_dir_path, "im_%02d.tiff" %ii)
        pic_param = basler.take_pic(basler_img_path)
        pic_param_data.append(pic_param)

        arecont_img_path = os.path.join(work_dir_path, "im_arecont_%02d.jpeg" %ii)
        if arecont_img is not None:
            with open(arecont_img_path, "wb") as f:
                f.write(arecont_img)

        rs_depth_path = os.path.join(work_dir_path, "rs_depth_%02d" %ii)
        rs_rgb_path = os.path.join(work_dir_path, "rs_rgb_%02d.png" %ii)
        np.save(rs_depth_path, depth)
        cv.imwrite(rs_rgb_path, rgb)

    basler.close_cam()
    rs_cam.rs_stop()
    basler_data["pic_params"] = pic_param_data
    with open(os.path.join(work_dir_path, "basler.json"), "w") as log:
        json.dump(basler_data, log)

    disk_space = get_disk_space()
    if disk_space < 10:  # space in GB
        print("-------------------")
        print("Warning: free disk space %0.1f" %disk_space)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', help='Measurement label')
    parser.add_argument('--note', help='Measurement note', default=None)
    args = parser.parse_args()

    main(args.label, args.note)
