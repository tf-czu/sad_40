"""
    Damage detection from images
"""

import csv
import os
import datetime

import cv2
import numpy as np

SCALE_SIZE = [9.8, 32.5]


def show_im(im):
    cv2.namedWindow("win_test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("win_test", 1068, 712)
    cv2.imshow("win_test", im)
    cv2.waitKey(0)
    cv2.destroyWindow("win_test")


def get_varieties_dict(path):
    ret_dict = {}
    with open(path) as dic_file:
        csv_reader = csv.reader(dic_file, delimiter=',')
        for label, variety in csv_reader:
            ret_dict[label] = variety

    return ret_dict


def get_scale(im):
    w, h = SCALE_SIZE
    # gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    b, g, r = cv2.split(im)
    gray = r
    __, bin_im = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY_INV)
    bin_im = cv2.morphologyEx(bin_im, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)))
    bin_im = cv2.morphologyEx(bin_im, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
    contours, __ = cv2.findContours(bin_im, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 200_000:
            return w*h/area

    return None


def get_circle(p1, p2, p3):
    # https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
    p1 = complex(*p1)
    p2 = complex(*p2)
    p3 = complex(*p3)
    w = p3 - p1
    w /= p2 - p1
    c = (p2 - p1) * (w - abs(w)**2) / 2j / w.imag + p1  # multiplied by -1

    return int(round(c.real)), int(round(c.imag)), int(round(abs(c-p1)))


def calculate_areas(points, im):
    ret = []
    for ii in range(2):
        im1 = np.zeros_like(im[:, :, 0])
        im2 = np.zeros_like(im[:, :, 0])
        im3 = np.zeros_like(im[:, :, 0])
        p1, p2, p3, p4 = points[ii*4:4*(ii+1)]  # border points p1 and p3, apple skin p2, damage peak p4
        # Circle on apple skin:
        cx, cy, r = get_circle(p1, p2, p3)
        cv2.circle(im1, (cx, cy), r, 255, -1)
        # Circle on apple skin:
        cx, cy, r = get_circle(p1, p4, p3)
        cv2.circle(im2, (cx, cy), r, 255, -1)
        mask = np.logical_and(im1!=0, im2!=0)
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        assert len(contours) == 1
        cnt = contours[0]
        area = cv2.contourArea(cnt)
        color = np.mean(im[mask], 0)
        ret.append([area, cnt, color])

    return ret


class ImageProcessing:
    def __init__(self):
        self.last_mpoint = None

    def manual_label(self, event, x, y, flags, param):
        """
        The function is called during all mouse events.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            # print(x, y)
            self.last_mpoint = (x, y)


    def image_processing(self, data):
        ii = 0
        cv2.namedWindow("win", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("win", 1068, 712)
        while True:
            if ii < 0:
                ii = 0
            if ii >= len(data):
                ii = len(data) - 1

            label, variety, im_id, img, points, res = data[ii]
            im_to_show = img.copy()
            for p in points:
                cv2.drawMarker(im_to_show, p, (255, 0, 0), cv2.MARKER_CROSS, markerSize=30, thickness=4)
            cv2.putText(im_to_show, f"{label}, {im_id}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=(255, 0, 0), thickness=5)
            for r in res:
                area, cnt, __ = r
                cv2.drawContours(im_to_show, [cnt], -1, (255, 0, 0), 2)

            cv2.imshow("win", im_to_show)
            cv2.setMouseCallback('win', self.manual_label)

            k = cv2.waitKey(100) & 0xFF
            if self.last_mpoint and len(points) < 8:
                points.append(self.last_mpoint)
                self.last_mpoint = None

            if k == ord("c"):
                if len(points) == 8:
                    scale = get_scale(img)
                    (area1, cnt1, color1), (area2, cnt2, color2) = calculate_areas(points, im_to_show)
                    res = (area1*scale, cnt1, color1), (area2*scale, cnt2, color2)

            if k == ord("d"):  # delete points
                points = []

            if k == ord("r"):
                res = []

            data[ii][-1] = res
            data[ii][-2] = points

            if k == ord("n"):  # next img
                ii += 1
            elif k == ord("b"):  # back one img
                ii -= 1
            elif k == ord("q"):  # close and save
                break

        cv2.destroyAllWindows()
        return data


def main_processing(img_path, dict_path):
    varieties_dict = get_varieties_dict(dict_path)
    data = []
    for label, variety in varieties_dict.items():
        assert label in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
        im_dir = f"jabka_mech-prop-{label}"
        variety_im_path = os.path.join(img_path, im_dir)
        img_list = sorted(os.listdir(variety_im_path))
        for ii, im_file in enumerate(img_list):
            assert str(ii) in im_file
            im = cv2.imread(os.path.join(variety_im_path, im_file))
            data.append([label, variety, ii, im, [], []])  # the last variables are for label points and results

    processing = ImageProcessing()
    data = processing.image_processing(data)
    csv_filename = datetime.datetime.now().strftime("apple_%y%m%d_%H%M%S.csv")
    with open(csv_filename, "w", newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",")
        csv_writer.writerow(["label", "apple ID", "variety", "repetition", "area (mm2)", "r", "g", "b"])
        for label, variety, im_id, img, points, res in data:
            for ii, (area, cnt, (b, g, r)) in enumerate(res):
                csv_writer.writerow([label, im_id, variety, ii+1, area, r, g, b])



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--img_path', '-i', help='Path to images', default='images/')
    parser.add_argument('--dict', '-d', help='Path to varieties dict file.', default='varieties_dict.csv')
    args = parser.parse_args()

    main_processing(args.img_path, args.dict)
