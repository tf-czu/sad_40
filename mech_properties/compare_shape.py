"""
    Load all logs and draw in one fig
"""

from matplotlib import pyplot as plt
import numpy as np

from press_processing import load_all


def load_and_draw(directory):
    data = load_all(directory)
    deform_steps = np.arange(0.2, 5.2, 0.2)
    force_data = np.zeros((len(data), len(deform_steps)))
    force_data[:, :] = np.nan
    for ii, (forces, deform, fig_path) in enumerate(data):
        for jj, step in enumerate(deform_steps):
            val_id = np.argmin(abs(deform - step))
            force_data[ii, jj] = forces[val_id]

    mean_val = np.mean(force_data, 0)
    assert len(mean_val) == len(deform_steps), len(mean_val)

    fig, ax1 = plt.subplots(1, 1, figsize=(4, 4))
    # ax1.plot(deform_steps, mean_val, "k.", label="Force")
    standard_dev = np.std(force_data, 0)
    ax1.errorbar(deform_steps, mean_val, yerr=standard_dev, fmt='ko', capsize=5, ecolor='k', elinewidth=1.5)

    ax1.set_xlabel("Deformation (mm)")
    ax1.set_ylabel("Force (N)")

    # plt.show()
    plt.savefig("compare_shape.png", dpi=1200)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Path to data directory')
    args = parser.parse_args()

    load_and_draw(args.directory)