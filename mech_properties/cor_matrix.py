"""
    Draw correlation matrix
"""
import csv

import numpy as np

from stat_tools.cor_mat import plot_cor_matrix


def load_data(csvfile):
    data = []
    with open(csvfile, mode='r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=',')
        params = next(csv_reader)[2:]
        assert len(params) == 7
        for row in csv_reader:
            line_data = [float(val) for val in row[2:]]
            data.append(line_data)

    return np.asarray(data), params


def draw_matrix(data, variables):
    plot_cor_matrix(data, variables)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csvfile', help='Path to csv file')
    args = parser.parse_args()

    data, variables = load_data(args.csvfile)
    draw_matrix(data, variables)
