import sys

import numpy as np
import cv2
# from matplotlib import pyplot as plt

from osgar.logger import LogReader, lookup_stream_id
from osgar.lib.serialize import deserialize


def main(logname):
    log = LogReader(logname, only_stream_id=0)
    print("original args:", next(log)[-1])

    only_im = lookup_stream_id(logname, "oak_camera.color")
    only_depth = lookup_stream_id(logname, "oak_camera.depth")
    only_pose3d = lookup_stream_id(logname, "localization.pose3d")
    print(only_im, only_depth, only_pose3d)

    with LogReader(logname, only_stream_id=[only_im, only_depth, only_pose3d]) as log:
        cv2.namedWindow("win", cv2.WINDOW_NORMAL)
        for timestamp, stream_id, data in log:
            if stream_id == only_im:
                buf_color = deserialize(data)
                color_im = cv2.imdecode(np.frombuffer(buf_color, dtype=np.uint8), 1)
                cv2.imshow("win", color_im)
                k = cv2.waitKey(1) & 0xFF
                if k == ord("q"):
                    break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    logname = sys.argv[1]
    main(logname)