"""Plot epsilon decay."""

import argparse

import matplotlib.pyplot as plt


if __name__ == "__main__":
    prs = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    prs.add_argument("-e", dest="epsilon", type=float, required=True, help="Epsilon\n")
    prs.add_argument("-d", dest="decay", type=float, required=True, help="Epsilon\n")
    prs.add_argument("-m", dest="minimum", type=float, required=True, help="Minimum Epsilon\n")
    prs.add_argument("-l", dest="length", type=int, required=True, help="Length\n")
    args = prs.parse_args()

    agent_steps = args.length // 5
    plt.plot([i * 5 for i in range(0, agent_steps)], [max(args.epsilon * args.decay**i, args.minimum) for i in range(0, agent_steps)], label='Curve with minimum')
    plt.plot([i * 5 for i in range(0, agent_steps)], [args.epsilon * args.decay**i for i in range(0, agent_steps)], label='Curve absolutist')

    plt.legend()
    plt.grid()
    plt.show()
