"""
    Usage: TODO

    In case using the osgar source code: export PYTHONPATH=<osgar directory>
"""
import sys
import time
import numpy as np
import cv2
from matplotlib import pyplot as plt

from osgar.logger import LogReader, lookup_stream_id
from osgar.lib.serialize import deserialize


def view_data(log_file):
    log = LogReader(log_file, only_stream_id=0)
    print("original args:", next(log)[-1])
    #only_stream_depth = lookup_stream_id(log_file, "d_camera.depth")
    only_stream_depth = lookup_stream_id(log_file, "app.depth")
    only_stream_color = lookup_stream_id(log_file, "app.color")
    with LogReader(log_file, only_stream_id=[only_stream_depth, only_stream_color]) as log:
        fig = plt.figure(figsize=(16, 10))
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        start = True
        new_depth, new_color = False, False
        for timestamp, stream_id, data in log:
            if stream_id == only_stream_depth:
                buf_depth = deserialize(data)
                depth_im = np.array(buf_depth, np.float64)
                new_depth = True

            if stream_id == only_stream_color:
                buf_color = deserialize(data)
                color_im = cv2.imdecode(np.frombuffer(buf_color, dtype=np.uint8), 1)
                new_color = True

            if new_color and new_depth:
                if start:
                    im1 = ax1.imshow(depth_im, vmin=400, vmax=2000)
                    im2 = ax2.imshow(color_im)
                    start = False
                im1.set_data(depth_im)
                im2.set_data(color_im)
                plt.draw()
                plt.pause(0.2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit()
    view_data(sys.argv[1])
