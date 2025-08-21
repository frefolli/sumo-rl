"""Epsilon Greedy Exploration Strategy."""
from __future__ import annotations

import numpy as np


class EpsilonGreedy:
    """Epsilon Greedy Exploration Strategy."""

    def __init__(self, initial_epsilon=1.0, min_epsilon=0.0, decay=0.99):
        """Initialize Epsilon Greedy Exploration Strategy."""
        self.initial_epsilon = initial_epsilon
        self.epsilon = initial_epsilon
        self.min_epsilon = min_epsilon
        self.decay = decay
        print('LOG', self.to_dict())

    def choose(self, q_table, state, action_space):
        """Choose action based on epsilon greedy strategy."""
        if np.random.rand() < self.epsilon:
            action = int(action_space.sample())
        else:
            action = np.argmax(q_table[state])

        self.epsilon = max(self.epsilon * self.decay, self.min_epsilon)
        # print(self.epsilon)
        return action

    def reset(self):
        """Reset epsilon to initial value."""
        self.epsilon = self.initial_epsilon

    def to_dict(self) -> dict:
      return {
        'initial_epsilon': self.epsilon,
        'min_epsilon': self.min_epsilon,
        'decay': self.decay
      }

    @staticmethod
    def from_dict(rep: dict) -> EpsilonGreedy:
      initial_epsilon = float(rep['initial_epsilon'])
      min_epsilon = float(rep['min_epsilon'])
      decay = float(rep['decay'])
      return EpsilonGreedy(initial_epsilon=initial_epsilon, min_epsilon=min_epsilon, decay=decay)
