"""
    Control static GUI for SAD 4.0 project
"""
import sys

from zmq_node import push_msg, ZmqPull
from threading import Thread, Event
import cv2
import numpy as np

from appJar import gui
app = gui(showIcon = False)


def load_image(data):
    return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), 1)


class ControlStatic:
    def __init__(self):
        self.server = ZmqPull()
        self.thread = None
        app.registerEvent(self.pull_data)
        self.prev_images = ["basler_prev", "arecont_prev", "rs_prev", "depth_prev"]
        self.counter = 0
        self.runnig = False
        self.last_label = ""
        self.reverse_direction = False
        self.exit_event = Event()
        for name in self.prev_images:
            setattr(self, name, None)

    def set_label(self):
        last_label = self.last_label
        reverse_direction = app.getCheckBox("Reverse")
        assert len(last_label) > 3, last_label
        num_part = last_label[-3:]  # max number is 999
        assert num_part.isnumeric(), num_part
        if reverse_direction == True:
            new_num = max(0, int(num_part) - 1)
        else:
            new_num = min(999, int(num_part) + 1)
        app.setEntry("label", f"{last_label[:-3]}{new_num:03d}")

    def pull_data(self):
        if not self.runnig:
            return
        if self.images and self.counter < 30:
            print("pull")
            for prev_name in self.images.copy():
                data = getattr(self.server, prev_name)
                if data is not None:
                    self.images.remove(prev_name)
                    img = load_image(data)
                    setattr(self, prev_name, img)
                    print(prev_name)
            self.counter += 1

        else:
            for name in self.prev_images:
                img = getattr(self, name)
                setattr(self, name, None)
                if img is not None:
                    cv2.imshow(name, img)

            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.counter = 0
            self.set_label()
            self.runnig = False


    def on_button_measure(self):
        if self.runnig:
            return
        self.images = self.prev_images.copy()
        label = app.getEntry("label")
        self.last_label = label
        if self.thread is not None:
            self.thread.join(2)

        self.thread = Thread(target=self.server.pull_msg, daemon=True)
        self.server.clear_images()
        self.thread.start()
        self.runnig = True
        push_msg(label)

    def main(self):
        app.setResizable(canResize=False)
        app.setTitle("Sad 4.0")
        app.setSticky("news")
        app.addEntry("label", row=0, column=0)
        # app.setEntry("label", "labell")
        app.addButton("measure_button", self.on_button_measure, row=0, column=1)
        app.setButton("measure_button", "Measure")
        app.addCheckBox("Reverse", row=1, column=1)

        app.go()

    # context manager functions
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if self.thread:
            self.thread.join(2)
            print(self.thread.is_alive())


if __name__ == "__main__":
    with ControlStatic() as monitor:
        monitor.main()
