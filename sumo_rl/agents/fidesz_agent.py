"""Fidesz Agent class."""

import pickle
import typing
from sumo_rl.agents.agent import Agent
from sumo_rl.environment.traffic_signal import TrafficSignal

class FideszAgent(Agent):
  """Fidesz Agent class."""

  def __init__(self, id: str,
                     controlled_entities: dict[str, TrafficSignal],
                     action_space,
                     cycle_time: int = 6):
    """Initialize Fidesz agent."""
    super().__init__(id)
    self.controlled_entities = controlled_entities
    self.action_space = action_space
    self.previous_actions = {ID: 0 for ID in self.controlled_entities}
    self.current_actions = self.previous_actions
    self.steps_from_last_action = 0
    self.cycle_time_steps = cycle_time
    self.history: list[tuple] = []
    self.previous_states = {}
    self.current_states = {}

  def reset(self):
    self.previous_actions = {ID: 0 for ID in self.controlled_entities}
    self.current_actions = self.previous_actions
    self.steps_from_last_action = 0

  def hard_reset(self) -> None:
    self.reset()

  def observe(self, observations: dict[str, tuple]):
    """Nothing is observed"""
    self.previous_states = self.current_states
    self.current_states = {ID: observations[ID] for ID in self.controlled_entities.keys()}

  def act(self) -> dict[str, int]:
    """Choose action cyclicly"""
    self.steps_from_last_action += 1
    if self.steps_from_last_action >= self.cycle_time_steps:
      actions = {}
      for ID in self.controlled_entities:
        actions[ID] = (self.previous_actions[ID] + 1) % self.action_space.n
      self.previous_actions = actions
      self.steps_from_last_action = 0
      return actions
    else:
      return self.previous_actions

  def learn(self, rewards: dict[str, typing.Any]):
    """Update history with new experience."""
    for ID in self.controlled_entities.keys():
      previous_state = self.previous_states[ID]
      current_state = self.current_states[ID]
      previous_action = self.previous_actions[ID]
      reward = rewards[ID]
      self.history.append((previous_state, previous_action, current_state, reward))

  def serialize(self, output_filepath: str) -> None:
    """Serialize Agent "memory" into an output file
    """
    with open(output_filepath, mode="wb") as file:
      pickle.dump(self.history, file)

  def deserialize(self, input_filepath: str) -> None:
    """Deserialize Agent "memory" from an input file
    """
    with open(input_filepath, mode="rb") as file:
      self.history = pickle.load(file)

  def __repr__(self) -> str:
    return "%s(%s)" % (self.__class__.__name__, list(self.controlled_entities.keys()))

  def can_be_serialized(self) -> bool:
    """True if serialization/deserialization is supported
    """
    return True

  def can_observe(self) -> bool:
    """True if observing is supported
    """
    return True

  def can_learn(self) -> bool:
    """True if learning is supported
    """
    return True
