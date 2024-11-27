"""
    Annalise data form universal testing machine
"""
import os
import sys

import numpy as np
from matplotlib import pyplot as plt

SMOOT_INTERVAL = 3
FORCE_SCALE = 1.979


def discrete_derivative(x_data, y_data, interval = 10):
    assert len(x_data) == len(y_data), (len(x_data), len(y_data))
    n = len(y_data) - interval
    x_ret = []
    y_ret = []
    for ii in range(n):
        x = x_data[ii: ii + interval]
        y = y_data[ii: ii + interval]
        slope, intercept = np.polyfit(x, y, 1)
        x_ret.append((x[0] + x[-1])/2)
        y_ret.append(slope)

    return x_ret, y_ret


def cut_data(time, force, positions):
    # touch detection
    is_force_change = np.diff(force) < -0.05
    assert True in is_force_change
    start = np.argmax(is_force_change)  # first true occurrence
    # detection of machine return
    is_position_increase = np.diff(positions) > 50
    if not (True in is_position_increase):
        end = -1
    else:
        end = np.argmax(is_position_increase)  # first true occurrence
        assert start < end, (start, end)

    assert (positions[start] - positions[end]) > 4900,\
        (positions[start] - positions[end], positions[start], positions[end])

    return time[start:end], force[start:end], positions[start:end]


def load_data(log_file):
    time_stamps = []
    forces = []
    positions = []
    with open(log_file) as datafile:
        for line in datafile:
            if "#" in line:
                continue  # skip file header

            data = line.split("\t")
            assert len(data) == 3, data
            try:
                t, f, p = [float(num) for num in data]
            except ValueError:
                sys.exit(f"Can not convert string to float in {log_file}: {data}")

            time_stamps.append(t)
            forces.append(f)
            positions.append(p)

    time_stamps, forces, positions = cut_data(np.array(time_stamps), np.array(forces), np.array(positions))
    forces = -forces * FORCE_SCALE
    deform = (positions[0] - positions)/1000

    return forces, deform  # time is not needed yet


def draw_sample(forces, deform, dir, fig_name):
    # prepare data
    n = SMOOT_INTERVAL
    smoothed_force = np.convolve(forces, np.ones(n)/n, mode='valid')
    smoothed_deform = np.convolve(deform, np.ones(n)/n, mode='valid')

    deform_2, d_force = discrete_derivative(deform, forces, interval=20)
    deform_3, dd_force = discrete_derivative(deform_2, d_force, interval=20)
    deform_4, dd_force_2 = discrete_derivative(deform_2, d_force, interval=400)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))
    ax1.plot(deform, forces, "k.", label= "Raw force")
    # ax1.plot(deform[n//2:len(smoothed_force)+n//2], smoothed_force, "r-", label="Smoothed_force")
    ax1.plot(smoothed_deform, smoothed_force, "r-", label="Smoothed Force")
    ax1.set_xlabel("Deformation (mm)")
    ax1.set_ylabel("Force (N)")
    ax1.legend()

    ax2.plot(deform_2, d_force, "k-")
    ax2.set_xlabel("Deformation (mm)")
    ax2.set_ylabel("Force derivation (N mm$^{-1}$)")

    ax3.plot(deform_3, dd_force, "k-")
    ax3.set_xlabel("Deformation (mm)")
    ax3.set_ylabel("2. Force derivation (N mm$^{-2}$)")

    ax4.plot(deform_4, dd_force_2, "k-")
    ax4.set_xlabel("Deformation (mm)")
    ax4.set_ylabel("2. Force derivation (N mm$^{-2}$)")

    # plt.show()
    # assert False
    fig_path = os.path.join(dir, "tmp", fig_name)
    plt.savefig(fig_path, dpi=500)
    plt.close()


def draw_all_data(dir):
    items_in_dir = sorted(os.listdir(dir))
    for item in items_in_dir:
        file_path = os.path.join(dir, item)
        if os.path.isfile(file_path) and "thr_" in item:
            print(item)
            forces, deform = load_data(file_path)
            fig_name = item.replace(".txt", ".png")
            draw_sample(forces, deform, dir, fig_name)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Path to data directory')
    args = parser.parse_args()

    draw_all_data(args.directory)
