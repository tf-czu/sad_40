"""
    Force - deformation relationship
"""

from matplotlib import pyplot as plt
import numpy as np

from press_processing import load_data, prepper_data


def calculate_r2(y_true, y_pred):  # TODO move to stat tools
    """
    Calculate coefficient of determination (R^2).

    Parameters:
    y_true (numpy.ndarray)
    y_pred (numpy.ndarray)

    Return:
    float: R^2.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # 1. Sum of Squares of Residuals
    ss_res = np.sum((y_true - y_pred)**2)

    # 2. Total Sum of Squares
    y_true_mean = np.mean(y_true)
    ss_tot = np.sum((y_true - y_true_mean)**2)

    if ss_tot == 0:
        if ss_res == 0:
            return 1.0
        else:
            return 0.0

    else:
        r2 = 1 - (ss_res / ss_tot)
        return r2


def draw_fig(force, deform):
    fig, ax1 = plt.subplots(1, 1, figsize=(4, 4))
    ax1.plot(deform, force, "k.", label="Force")

    smoothed_deform, smoothed_force, [x_a, f_a], [x_max, f_max] = prepper_data(deform, force)
    assert f_a == 51.099759, f_a
    assert x_a == 1.4157253333333306, x_a
    ax1.plot(x_a, f_a, "r+", label="Fa")
    ax1.plot(x_max, f_max, "r+", label="Fb")

    a_id = np.argmin(abs(deform - x_a))
    coeff = np.polyfit(deform[:a_id], force[:a_id], 1)
    k_a, intercept = coeff
    print(f"k_a: {k_a}, intercept: {intercept}")
    pa = np.poly1d(coeff)
    ax1.plot(deform[:a_id], pa(deform[:a_id]), "r--", label="Line")
    r2  = calculate_r2(force[:a_id], pa(deform[:a_id]))
    print(f"R2: {r2}")

    rear_id = np.argmin(abs(deform - (x_max + 1)))
    rear_average = np.mean(force[rear_id:])
    ax1.plot([x_max + 1, 5], [rear_average, rear_average], "r--", label="Ft")

    ax1.set_xlabel("Deformation (mm)")
    ax1.set_ylabel("Force (N)")

    # plt.show()
    plt.savefig("force-deform.png", dpi=1200)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logfile', help='Path to data file')
    args = parser.parse_args()

    assert "thr_E_09" in args.logfile, args.logfile

    force, deform = load_data(args.logfile)
    draw_fig(force, deform)
