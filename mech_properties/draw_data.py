"""
    Plots data from apple testing during 2022 season.
"""

import csv

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

PENDULUM_DATA = "data/otlaky-data-kyvadlo_221103.csv"
IMAGE_DATA = "apple_data_images.csv"


def load_data():
    # pendulum
    pendulum_data = {}
    with open(PENDULUM_DATA) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            variety = row[1]
            if variety == "Variety" or len(row) != 11:
                continue
            delta_c1 = float(row[8]) - float(row[7])
            delta_c2 = float(row[10]) - float(row[9])
            if variety in pendulum_data:
                pendulum_data[variety].extend([delta_c1, delta_c2])
            else:
                pendulum_data[variety] = [delta_c1, delta_c2]
    # images
    images_data = {}
    with open(IMAGE_DATA) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            variety = row[2]
            if variety == "variety" or len(row) != 8:
                continue
            area = float(row[4])
            if variety in images_data:
                images_data[variety].append(area)
            else:
                images_data[variety] = [area]

    return pendulum_data, images_data


def cor_data(pen_data, img_data):
    # all
    pen_sampel_75 = []
    pen_sampel_45 = []
    for values in pen_data.values():
        pen_sampel_75.extend(values[:10])
        pen_sampel_45.extend(values[10:])
    img_sampel_75 = []
    img_sampel_45 = []
    for values in img_data.values():
        img_sampel_75.extend(values[:10])
        img_sampel_45.extend(values[10:])

    r_val, p_value = stats.pearsonr(pen_sampel_75, img_sampel_75)
    print(f"Pearson 75: {r_val}, {p_value}")
    r_val, p_value = stats.pearsonr(pen_sampel_45, img_sampel_45)
    print(f"Pearson 45: {r_val}, {p_value}")

    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111)
    ax.plot(pen_sampel_75, img_sampel_75, "r+", label="75 deg")
    ax.plot(pen_sampel_45, img_sampel_45, "b+", label="45 deg")
    ax.set_xlabel("Elasticity difference(-)")
    ax.set_ylabel("Damage area (mm$^2$)")
    ax.legend()
    plt.savefig("Correlation.png", dpi=500)
    # plt.show()


def box_all(pen_data, img_data):
    pen_45 = []
    pen_75 = []
    names = []
    for key, values in pen_data.items():
        names.append(key)
        pen_45.append(values[10:])
        pen_75.append(values[:10])
    imdata_45 = []
    imdata_75 = []
    for key, values in img_data.items():
        imdata_45.append(values[10:])
        imdata_75.append(values[:10])

    y_labels = ["Elasticity difference(-)", "Elasticity difference(-)", "Damage area (mm$^2$)", "Damage area (mm$^2$)"]
    graph_types = ["pen_45", "pen_75", "imdata_45", "imdata_75"]
    for data, y_label, graph_type in zip([pen_45, pen_75, imdata_45, imdata_75], y_labels, graph_types):
        fig = plt.figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        x = list(range(1,13))
        ax.set_ylabel(y_label, fontsize=10)
        print(x, names)
        # plt.xticks(x, names, fontsize=10)  # , fontweight = "bold")
        ax.set_xticklabels(names)
        # ax.set_yticks(fontsize=9)
        bp = ax.boxplot(data, sym="k+", notch=False)
        plt.setp(bp['boxes'], color="k")
        plt.setp(bp['whiskers'], color="k")
        plt.setp(bp['caps'], color="k")
        plt.setp(bp['medians'], color="k")

        plt.savefig(f"boxplot_{graph_type}", dpi=800)
        # plt.show()
        plt.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('choice', choices=["box_all", "cor"], default="box_all", help='choice variant')

    args = parser.parse_args()
    pen_data, img_data = load_data()
    print(args.choice)
    if args.choice == "cor":
        cor_data(pen_data, img_data)
    if args.choice == "box_all":
        box_all(pen_data, img_data)