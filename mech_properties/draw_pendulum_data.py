"""
    Just draw pendulum raw data
"""
import sys
import csv
import os

from matplotlib import pyplot as plt
import numpy as np


def draw_data(data_path):
    csv_list = os.listdir(data_path)
    for csv_name in csv_list:
        assert csv_name.endswith(".csv"), csv_name
        with open(os.path.join(data_path, csv_name)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            x1_list = []
            x2_list = []
            for line in csv_reader:
                x1, x2 = line
                if x1:
                    x1_list.append(int(x1))
                if x2:
                    x2_list.append(int(x2))

            plt.plot(np.arange(len(x1_list)), x1_list)
            plt.plot(np.arange(len(x2_list)), x2_list)
            plt.savefig(f"tmp/{csv_name[:-3]}png")
            plt.close()


if __name__ == "__main__":
    draw_data(sys.argv[1])
