"""
    Annalise data form universal testing machine
"""
import os
import sys
import csv

import numpy as np
from matplotlib import pyplot as plt

SMOOT_INTERVAL = 3
FORCE_SCALE = 1.979


def write_data(data, csv_file_name):
    with open(csv_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(["id", "Fa", "k_a", "Fb", "Fa/Fb", "Ft", "rear_slope"])  # header
        for item in data:
            writer.writerow(item)

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


def get_first_f_peak(x, y):  # copy paste from cereal_monitor
    yd = np.diff(y)
    ydd = np.diff(yd)
    ex = yd[:-1] * yd[1:]
    y_max = np.logical_and(ex <= 0, ydd < 0)
    assert len(y_max) >= 0
    y_ret = y[1:-1][y_max][0]
    x_ret = x[1:-1][y_max][0]

    return x_ret, y_ret


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
    # limit to 5 mm
    limit_id = np.argmin(abs(deform - 5))

    return forces[:limit_id], deform[:limit_id]  # time is not needed yet


def draw_sample(forces, deform, fig_path):
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
    plt.savefig(fig_path, dpi=500)
    plt.close()


def load_all(dir_name):
    data = []
    items_in_dir = sorted(os.listdir(dir_name))
    for item in items_in_dir:
        file_path = os.path.join(dir_name, item)
        if os.path.isfile(file_path) and "thr_" in item:
            forces, deform = load_data(file_path)
            fig_name = item.replace(".txt", ".png")
            fig_path = os.path.join(dir_name, "tmp", fig_name)
            data.append([forces, deform, fig_path])

    return data


def draw_all_data(dir_name):
    data = load_all(dir_name)
    for forces, deform, fig_path in data:
        print(fig_path)
        draw_sample(forces, deform, fig_path)

def prepper_data(deform, force):
    n = SMOOT_INTERVAL
    smoothed_force = np.convolve(force, np.ones(n) / n, mode='valid')
    smoothed_deform = np.convolve(deform, np.ones(n) / n, mode='valid')
    x_a, f_a = get_first_f_peak(smoothed_deform, smoothed_force)
    f_max = max(smoothed_force)
    x_max = smoothed_deform[smoothed_force.argmax()]

    return smoothed_deform, smoothed_force, [x_a, f_a], [x_max, f_max]


class PlotAnnotation:
    def __init__(self, dir_name):
        self.dir_name = dir_name
        try:
            os.makedirs(os.path.join(self.dir_name, "tmp2"))
        except FileExistsError:
            print("The directory tmp2 already exist. Remove it!")
            sys.exit()
        self.last_key_event = None
        self.last_click_pose = None
        self.out_data = []  # to be added items: [label, Fa, k_a, Fb, Fa/Fb, Ft, rear_slope]

    def on_key(self, event):
        self.last_key_event = event.key

    def on_clik(self, event):
        self.last_click_pose = [event.xdata, event.ydata]

    def annotation(self, data):
        fig = plt.figure(figsize=(5, 5))
        fig.canvas.mpl_connect('key_press_event', self.on_key)
        fig.canvas.mpl_connect('button_press_event', self.on_clik)
        fig.subplots_adjust(left=0.15, bottom=0.15)
        ax1 = fig.add_subplot(111)
        plot_1, = ax1.plot([0, 1], [0, 1], "k+")  # define initial plot
        plot_rear, = ax1.plot([0, 1], [0, 1], "r-")
        # plot_rear_slope, = ax1.plot([0, 1], [0, 1], "y-")
        plot_a, = ax1.plot(0, 0, "ro")  # define initial plot
        plot_ap, = ax1.plot([0, 1], [0, 1], "r-")
        plot_max, = ax1.plot(0, 0, "ro")  # define initial plot
        
        ax1.set_xlabel("Deformace (mm)")
        ax1.set_ylabel("Síla (N)")

        ii = 0
        print(ii)
        while True:
            ii = max(0, min(len(data)-1, ii))
            forces, deform, fig_path = data[ii]
            label = os.path.basename(fig_path)[4:8]
            smoothed_deform, smoothed_force, [x_a, f_a], [x_max, f_max] = prepper_data(deform, forces)
            # print([x_a, f_a], [x_max, f_max])

            rear_id = np.argmin(abs(deform - (x_max + 1)))
            rear_average = np.mean(forces[rear_id:])
            coeff = np.polyfit(deform[rear_id:], forces[rear_id:], 1)
            rear_slope, intercept = coeff
            p_rear = np.poly1d(coeff)

            a_id = np.argmin(abs(deform - x_a))
            coeff = np.polyfit(deform[:a_id], forces[:a_id], 1)
            k_a, intercept = coeff
            pa = np.poly1d(coeff)

            plot_1.set_data(smoothed_deform, smoothed_force)
            plot_a.set_data([x_a], [f_a])
            plot_max.set_data([x_max], [f_max])
            plot_ap.set_data(deform[:a_id], [pa(deform[:a_id])])
            plot_rear.set_data([x_max + 1, 5], [rear_average, rear_average])
            #plot_rear_slope.set_data(deform[rear_id:], p_rear(deform[rear_id:]))

            ax1.relim()
            ax1.autoscale_view()

            plt.draw()
            plt.pause(0.5)

            if self.last_key_event == "right":
                self.last_key_event = None
                print(ii)
                ii += 1

            if self.last_key_event == "left":
                self.last_key_event = None
                print(ii)
                ii -= 1

            if self.last_key_event == "w":
                self.last_key_event = None
                self.out_data.append([label, f_a, k_a, f_max, f_a/f_max, rear_average, rear_slope])
                print(f"Saved item {ii}, {label}")
                plt.savefig(os.path.join(self.dir_name, "tmp2", f"thr_fig_{label}"), dpi=500)
                ii += 1

            if self.last_key_event == "e":
                plt.clf()
                write_data(self.out_data, os.path.join(self.dir_name, "out_data.csv"))
                break


def perform_annotation(dir_name):
    data = load_all(dir_name)
    annotate = PlotAnnotation(dir_name)
    annotate.annotation(data)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Path to data directory')
    parser.add_argument("--annotation", "-a", help="Annotate plots", action="store_true")
    args = parser.parse_args()

    if args.annotation:
        perform_annotation(args.directory)
    else:
        draw_all_data(args.directory)
