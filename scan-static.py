import os

from pypylon import pylon
import socket
import urllib.request
import pyrealsense2 as rs
import numpy as np
import datetime
import cv2 as cv

HOST = "192.168.1.100"  # Basler camera
STORAGE_PATH = "/home/ovosad/ovosad_data"

ARECONT_URL = "http://192.168.1.36/image?res=fullf&quality=12&doublescan=1&channel=color"
ARECONT_SET = "http://192.168.1.36/set?daynight=dual"

class Basler:
    def __init__(self):
        self.address = HOST
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
        self.cam.ExposureAuto.SetValue('Continuous')
#        self.cam.Gamma.SetValue(0.4)
        self.cam.GainAuto.SetValue("Continuous")
        #self.cam.GainRaw.SetValue(34)
#        a = self.cam.Gain.GetValue()

    def take_pic(self, file_path):
        self.cam.StartGrabbing()
        img = pylon.PylonImage()
        with self.cam.RetrieveResult(2000) as result:
            img.AttachGrabResultBuffer(result)
            img.Save(pylon.ImageFileFormat_Tiff, file_path)  # TODO filename!!

            img.Release()

        self.cam.StopGrabbing()

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
    work_dir_path = os.path.join(STORAGE_PATH, day_name, label_dir)
    os.mkdir(work_dir_path)

    basler = Basler()
    rs_cam = Realsense_cam()
    set_url = ARECONT_SET
    url = ARECONT_URL
    arecont = Arecont(set_url)

    for ii in range(5):
        arecont_img = arecont.arecont_take_pic(url)
        depth, rgb = rs_cam.rs_take_pic()
        basler_img_path = os.path.join(work_dir_path, "im_%02d.tiff" %ii)
        basler.take_pic(basler_img_path)

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



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', help='Measurement label')
    parser.add_argument('--note', help='Measurement note', default="")
    args = parser.parse_args()

    main(args.label, args.note)