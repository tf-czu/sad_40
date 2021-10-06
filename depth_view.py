"""
    Usage: e.g. python depth_view.py <logfile> --im <color_stream> --depth <depth_stream>

    In case using the osgar source code: export PYTHONPATH=<osgar directory>
"""

import numpy as np
import cv2
# from matplotlib import pyplot as plt

from osgar.logger import LogReader, lookup_stream_id
from osgar.lib.serialize import deserialize


def resize_if_needed(image):
    h, w, __ = image.shape
    if w != 480:
        h = int(round(h * 480 / w))
        assert h <= 850, h
        return cv2.resize(image, (480, h))

    return image


def view_data(log_file, im_stream, depth_stream, rot):
    log = LogReader(log_file, only_stream_id=0)
    print("original args:", next(log)[-1])
    only_im = lookup_stream_id(log_file, im_stream)
    only_depth = lookup_stream_id(log_file, depth_stream)

    im_data = []
    with LogReader(log_file, only_stream_id=[only_im, only_depth]) as log:
        for timestamp, stream_id, data in log:
            if stream_id == only_depth:
                buf_depth = deserialize(data)
                depth_data = np.array(buf_depth, np.float64)
                im_data.append([timestamp, stream_id, depth_data])

            if stream_id == only_im:
                buf_color = deserialize(data)
                color_im = cv2.imdecode(np.frombuffer(buf_color, dtype=np.uint8), 1)
                im_data.append([timestamp, stream_id, color_im])

    print(len(im_data))
    background = np.zeros((880, 960+480, 3), dtype=np.uint8)
    ii = 0
    last_image = None
    depth_im = None
    wait = 0
    while True:
        if ii < 0:
            ii = 0
        if ii >= len(im_data):
            ii = len(im_data) - 1

        timestamp, stream_id, image = im_data[ii]
        if stream_id == only_im:
            # color image
            if rot:
                image = np.rot90(image, k=3)
            last_image = resize_if_needed(image)
            im_height = last_image.shape[0]
            background[:im_height, :480, :] = last_image
            background[im_height:, :480, :] = 0
            cv2.putText(background, str(timestamp), (5, 878), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                        color=(255, 255, 255))

        if stream_id == only_depth:
            # depth data
            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            # https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/opencv_viewer_example.py
            depth_data = image
            depth_im = cv2.applyColorMap(cv2.convertScaleAbs(depth_data, alpha=0.03), cv2.COLORMAP_JET)
            if rot:
                depth_im = np.rot90(depth_im, k=3)
                depth_data = np.rot90(depth_data, k=3)

            depth_im = resize_if_needed(depth_im)
            im_height = depth_im.shape[0]
            depth_data = cv2.resize(depth_data, depth_im.shape[::-1][1:])
            #if ii ==50:
            #    plt.imshow(depth_data)
            #    plt.show()

            last_depth_mask = np.logical_and(depth_data > 100, depth_data < 5000)
            last_depth_mask3d = np.repeat(last_depth_mask, 3, axis=1).reshape(depth_im.shape)
            background[:im_height, 480:960, :] = depth_im
            background[im_height:, 480:, :] = 0
            cv2.putText(background, str(timestamp), (485, 878), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                        color=(255, 255, 255))
            if last_image is not None:
                sub_background = np.zeros(last_image.shape, dtype=np.uint8)
                sub_background[last_depth_mask3d] = last_image[last_depth_mask3d]
                background[:im_height, 960:, :] = sub_background

        cv2.imshow("win", background)

        k = cv2.waitKey(wait) & 0xFF
        if k == ord("n"):  # next img
            ii += 1
        elif k == ord("b"):  # back one img
            ii -= 1
        elif k == ord(" "):  # play/pause
            if wait:
                wait = 0
            else:
                wait = 50
        elif k == ord("s"):  # save images
            cv2.imwrite("background_im_%05d.jpg" %ii, background)
            cv2.imwrite("color_im_%05d.jpg" %ii, image)
            if depth_im is not None:
                cv2.imwrite("depth_im_%05d.jpg" % ii, depth_im)
        elif k == ord("q"):  # close and save
            break
        if wait:
            ii += 1

cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logfile', help='path to logfile')
    parser.add_argument('--im', help='image stream', default="app.color")
    parser.add_argument('--depth', help='depth stream', default="app.depth")
    parser.add_argument('--rot', help='rotate image 90 deg', action='store_true')
    args = parser.parse_args()

    im_stream = args.im
    depth_stream = args.depth

    view_data(args.logfile, im_stream, depth_stream, args.rot)
