"""
    Analysis of pendulum raw data.
    Run in sad-40 directory.
"""

import os
import csv
import matplotlib.pyplot as plt
import numpy as np


DATA_PATH = "mech_properties/data_2024"
DATA_FILE = "otlaky_2024.csv"

E_45 = 0.119 # J, kinetic energy during impact (angle 45 deg.)
E_75 = 0.301 # J, kinetic energy during impact (angle 75 deg.)
HEADER = ["Label", "hmotnost (g)", "vyska (mm)", "sirka (mm)", "sirka (mm)", "Objem", "Hustota", "Ek", "c11", "c12"]


def refl2E(Ek, ratio):
    if Ek == E_45:
        a = 45
    else:
        a = 75
    da = a*ratio
    assert da < a, [Ek, a, ratio]
    print(da, ratio)
    return (1-np.cos(np.deg2rad(da))) / (1-np.cos(np.deg2rad(a)))


def write_new_csv(data):
    file_name = os.path.join(DATA_PATH, "otlaky-data-kyvadlo.csv")
    with open(file_name, "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(HEADER)
        for row in data:
            csv_writer.writerow(row)


def get_break_points(y, n = 3):
    kernel = np.ones(n) / n
    # smooth the data
    y_s = np.convolve(y, kernel, mode="same")
    yd = np.diff(y_s)
    ydd = np.diff(yd)

    ex = yd[:-1] * yd[1:]
    break_points = np.where(ex <= 0)[0] + 1
    assert len(break_points) >= 2, break_points
    b1_arg, b2_arg = break_points[:2]
    assert ydd[b1_arg] > 0, [ydd[b1_arg], y[b1_arg], b1_arg]
    assert ydd[b2_arg] < 0, [ydd[b2_arg], y[b2_arg], b2_arg]

    return y[b1_arg], y[b2_arg], b1_arg, b2_arg


def pendulum_reflection(file_name, debug = False, n = 3):
    beat_1 = []
    beat_2 = []
    with open(os.path.join(DATA_PATH, "data", file_name)) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            b1, b2 = row
            if b1 != "":
                beat_1.append(int(b1))
            if b2 != "":
                beat_2.append(int(b2))

    b1_y1, b1_y2, b1_x1, b1_x2 = get_break_points(beat_1, n = n)
    b2_y1, b2_y2, b2_x1, b2_x2 = get_break_points(beat_2, n = n)

    if debug:
        print(b1_y1, b1_y2, b1_x1, b1_x2)
        print(b2_y1, b2_y2, b2_x1, b2_x2)
        plt.plot(beat_1, "k")
        plt.plot([b1_x1, b1_x2], [b1_y1, b1_y2], "ko")
        plt.plot(beat_2, "r")
        plt.plot([b2_x1, b2_x2], [b2_y1, b2_y2], "ro")
        plt.show()

    return abs((b1_y1 - b1_y2) / b1_y1), abs((b2_y1 - b2_y2)/b2_y1)  # reflection ratio


def get_file_name(key_string, file_list):
    ret = [name for name in file_list if key_string in name]
    assert len(ret) <= 1, ret
    if len(ret) == 0:
        return None
    return ret[0]


def load_data():
    # First load DATA_FILE as list
    main_data_in = []
    with open(os.path.join(DATA_PATH, DATA_FILE)) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            print(row)
            # assert len(row) == 8
            label = row[0]
            mass = float(row[1]) if row[1] else None
            height, d1, d2 = [float(num) for num in row[2:5]]
            volume = float(row[5])/0.997 if row[5] else None  # water density is 0.997 g/cm**2
            density =mass/volume if (volume and mass) else None

            main_data_in.append([label, mass, height, d1, d2, volume, density])

    # Load files list
    file_list = os.listdir(os.path.join(DATA_PATH, "data"))
    file_list = [item for item in file_list if "pendulum" in item]
    # assert len(file_list) == 180

    return main_data_in, file_list


def main():
    main_data_in, file_list = load_data()
    main_data_out = []
    ii = 0
    for label, mass, height, d1, d2, volume, density in main_data_in:  # One item represents data from one apple.
        print(label)
        apple_num = int(label[1:])
        Ek = E_45
        # Find relevant file name
        key_string = f"{label[0]}_{label[1:]}"
        pendulum_fn = get_file_name(key_string, file_list)
        if pendulum_fn is None:
            continue

        # if label in ["F20", "G08", "I09", "K05", "K06"]:
        #    debug = True
        # else:
        #     debug = False
        # n1 = n2 = 3
        # if label in ["G08", "I09", "K06"]:
        #     n2 = 5
        # if label in ["K05", "K06"]:
        #     n1 = 5
        debug = True
        n = 3
        b1_ratio_1, b1_ratio_2 = pendulum_reflection(pendulum_fn, debug = debug, n = n)

        main_data_out.append([label, mass, height, d1, d2, volume, density, Ek,
                                      refl2E(Ek, b1_ratio_1),
                                      refl2E(Ek, b1_ratio_2)
                                      ]
                             )
        ii += 1

    write_new_csv(main_data_out)


if __name__ == "__main__":
    main()
