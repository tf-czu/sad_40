"""
    Calculate and draw PCA
"""
import csv

import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler

from stat_tools.pca import perform_pca


def load_data(csvfile):
    data = []
    genotypes = []
    with open(csvfile, mode='r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=',')
        params = next(csv_reader)[2:]
        assert len(params) == 7
        for row in csv_reader:
            line_data = [float(val) for val in row[2:]]
            data.append(line_data)
            genotypes.append(row[1])

    return np.asarray(data), params, genotypes


def my_pca(data, variables, genotypes):
    # normalize data: z = (x - u) / s
    norm_data = np.zeros(data.shape)
    for ii in range(7):
        sub_data = data[:, ii]
        norm_sub = (sub_data - np.mean(sub_data)) / np.std(sub_data)
        norm_data[:, ii] = norm_sub
    (pc1, pc2, pc3), pca = perform_pca(norm_data, normalize_data=False, draw=False)
    fig = plt.figure(1, figsize=(5, 5))
    fig.subplots_adjust(top=0.95, bottom=0.25, left=0.15)
    ax = fig.add_subplot(111)

    genotypes = np.asarray(genotypes)
    color = ["bo", "ro", "go", "mo", "ko", "yo" ]
    for ii, item in enumerate(set(genotypes)):
        x_i = pc1[genotypes == item]
        y_i = pc2[genotypes == item]
        ax.plot(x_i, y_i, color[ii], label=item)

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})", fontsize=10)
    ax.legend(bbox_to_anchor=(0.5, -0.3), loc='lower center', ncol=3)

    components = pca.components_.T
    print(components)
    scale = 5
    for dx, dy in zip(components[:, 0], components[:, 1]):
        ax.arrow(0, 0, dx*scale, dy*scale, color="0.5", width=0.05)

    tx_labels = variables
    assert len(tx_labels) == components.shape[0]
    for (cx, cy, cz), s in zip(components, tx_labels):
        ax.text(cx*scale, cy*scale, s)

    # plt.show()
    plt.savefig("pca_plot.png", dpi=1200)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csvfile', help='Path to csv file')
    args = parser.parse_args()

    data, variables, genotypes = load_data(args.csvfile)
    my_pca(data, variables, genotypes)
