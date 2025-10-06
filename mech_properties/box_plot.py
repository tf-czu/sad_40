"""
    Compare all via box plots
"""
import csv

from matplotlib import pyplot as plt
from stat_tools.kruskal_test import kruskal_test
import scipy.stats as stats


def get_csv_data(csvfile):
    data = {}
    with open(csvfile, mode='r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=',')
        params = next(csv_reader)[2:]
        assert len(params) == 7
        for row in csv_reader:
            genotype = row[1]
            if genotype not in data:
                data[genotype] = {}
                for par, val in zip(params, row[2:]):
                    data[genotype][par] = [float(val)]
            else:
                for par, val in zip(params, row[2:]):
                    data[genotype][par].append(float(val))

    return data


def compare_data(data):
    fig = plt.figure(figsize=(6.5, 9))
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.05, top=0.95, hspace=0.4, wspace=0.15)
    x = [1, 2, 3, 4, 5, 6]
    genotypes = [genotype for genotype in data]
    parms_labels = ["Density", "Volume", "Pa", "Ka", "Pb", "Kf", "Pc"]
    parms_titles = ["Density (g cm$^{-3}$)", "Volume (cm$^3$)", "$Pa$ (MPa)", "$Ka$ (N mm$^{-1}$)", "$Pb$ (MPa)", "$Kf$ (-)", "$Pc$ (MPa)"]

    for ii, (parm, par_title) in enumerate(zip(parms_labels, parms_titles)):
        print(parm)
        print("------------------")
        sub_data = [data[gen][parm] for gen in genotypes]
        for d, gen in zip(sub_data, genotypes):
            shapiro_stat, shapiro_p = stats.shapiro(d)
            if shapiro_p <= 0.05:
                print("shapiro test: ", gen, parm, shapiro_p)
        print("------------------")
        kruskal_test(sub_data, names=genotypes)

        ax = fig.add_subplot(4, 2, ii + 1)

        bp = ax.boxplot(sub_data)
        plt.setp(bp['boxes'], color="k")
        plt.setp(bp['whiskers'], color="k")
        plt.setp(bp['caps'], color="k")
        plt.setp(bp['medians'], color="k")

        plt.xticks(x, genotypes, fontsize=8)
        plt.yticks(fontsize=8)
        plt.title(par_title, fontsize=10, loc="left")

    # plt.show()
    plt.savefig("box_plots", dpi=1200)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csvfile', help='Path to csv file')
    args = parser.parse_args()

    data = get_csv_data(args.csvfile)
    compare_data(data)
