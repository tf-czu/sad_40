"""
    TODO
"""
import cv2
from threading import Thread


class RouteCam:
    def __init__(self, config, bus):
        self.input_thread = Thread(target=self.run_input, daemon=True)
        self.bus = bus
        self.subsample = config.get('subsample', 1)
        self.continuously = config.get("continuously", True)
        if self.continuously:
            self.bus.register('image')
        else:
            self.bus.register('frame:null')
        rtsp_url = config.get("rtsp_url", "rtsp://192.168.1.55:5005/routecam")
        self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        self.set_camera()

    def set_camera(self):
        pass

    def start(self):
        self.input_thread.start()

    def join(self, timeout=None):
        self.input_thread.join(timeout=timeout)

    def run_input(self):
        counter = 0
        while self.bus.is_alive():
            # Capture frame-by-frame
            ret, frame = self.cap.read()
            counter += 1
            if ret and counter == self.subsample:
                if self.continuously:
                    retval, data = cv2.imencode('*.jpeg', frame)
                    if len(data) > 0:
                        self.bus.publish('image', data.tobytes())
                else:
                    self.bus.publish('frame', frame)
                counter = 0
        self.cap.release()

    def request_stop(self):
        self.bus.shutdown()
