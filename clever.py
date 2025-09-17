"""
This script attempted Experience Replay, failing
"""

import pickle
import numpy
import random
from sumo_rl.exploration.epsilon_greedy import EpsilonGreedy
from sumo_rl.models.commons import Timer
# python -m main -r -A dummy -O d -R dwt -P space -DT

State=tuple
Action=int
Reward=float

class DQLAgent:
  """Double Q-learning Agent class."""
  def __init__(self, number_of_actions: int):
    """Initialize Q-learning agent."""
    self.number_of_actions = number_of_actions
    self.qa_table = {}
    self.qb_table = {}
    self.alpha = 0.1
    self.gamma = 0.9
    self.exploration = EpsilonGreedy(1.0, 0.05, 0.99)

  def learn(self, episode: list[tuple[State, Action, State, Reward]]):
    """Update Q-table with new experience."""
    for (previous_state, previous_action, current_state, reward) in episode:
      if previous_state not in self.qa_table:
        self.qa_table[previous_state] = [0 for _ in range(self.number_of_actions)]
      if previous_state not in self.qb_table:
        self.qb_table[previous_state] = [0 for _ in range(self.number_of_actions)]
      if current_state not in self.qa_table:
        self.qa_table[current_state] = [0 for _ in range(self.number_of_actions)]
      if current_state not in self.qb_table:
        self.qb_table[current_state] = [0 for _ in range(self.number_of_actions)]
      qa_driven_action = numpy.argmax(self.qa_table[current_state])
      qb_driven_action = numpy.argmax(self.qb_table[current_state])
      self.qa_table[previous_state][previous_action] = self.qa_table[previous_state][previous_action] + self.alpha * (
        reward + self.gamma * self.qb_table[current_state][qa_driven_action] - self.qa_table[previous_state][previous_action]
      )
      self.qb_table[previous_state][previous_action] = self.qb_table[previous_state][previous_action] + self.alpha * (
        reward + self.gamma * self.qa_table[current_state][qb_driven_action] - self.qb_table[previous_state][previous_action]
      )

  def serialize(self, output_filepath: str) -> None:
    """Serialize Agent "memory" into an output file
    """
    with open(output_filepath, mode="wb") as file:
      pickle.dump((self.alpha, self.gamma, self.qa_table, self.qb_table, self.exploration.to_dict()), file)

  def deserialize(self, input_filepath: str) -> None:
    """Deserialize Agent "memory" from an input file
    """
    with open(input_filepath, mode="rb") as file:
      self.alpha, self.gamma, self.qa_table, self.qb_table, exp_rep = pickle.load(file)
      self.exploration = EpsilonGreedy.from_dict(exp_rep)

  def can_be_serialized(self) -> bool:
    """True if serialization/deserialization is supported
    """
    return True

  def can_learn(self) -> bool:
    """True if learning is supported
    """
    return True

  def can_observe(self) -> bool:
    """True if observing is supported
    """
    return True

def main():
  timer = Timer()
  history: list[tuple[State, Action, State, Reward]]
  with open("outputs/agents/final/SSOSdensity-2-6SO-2SS.pickle", "rb") as file:
    history = pickle.load(file)
  timer.round('History length: %s' % len(history))
  actions = {a:0 for (_,a,_,_) in history}
  timer.round('Action space: %s' % len(actions))
  agent = DQLAgent(len(actions))
  number_of_episodes = 1600
  episode_length = 6000
  for episode_num in range(number_of_episodes):
    episode = random.choices(history, k=episode_length)
    timer.round('Episode #%s START' % episode_num)
    agent.learn(episode)
    timer.round('Episode #%s END' % episode_num)
    if episode_num % 100 == 0:
      agent.serialize('./clever-agent.pickle')
  agent.serialize('./clever-agent.pickle')
  total_length = (number_of_episodes * episode_length)
  total_length_in_seconds = total_length * 5
  total_length_in_hours = total_length_in_seconds / 3600
  total_length_in_days = total_length_in_hours / 24
  print('Length in days:', total_length_in_days)

if __name__ == '__main__':
  main()
