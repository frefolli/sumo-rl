"""Plot epsilon decay."""

import argparse

import matplotlib.pyplot as plt


if __name__ == "__main__":
    prs = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    prs.add_argument("-e", dest="epsilon", type=float, required=True, help="Epsilon\n")
    prs.add_argument("-d", dest="decay", type=float, required=True, help="Epsilon\n")
    prs.add_argument("-l", dest="length", type=int, required=True, help="Length\n")
    args = prs.parse_args()

    plt.plot([i for i in range(0, args.length, 5)], [args.epsilon * args.decay**i for i in range(0, args.length // 5)])

    plt.grid()
    plt.show()
