"""Dummy Agent class.

Instead of learning it actually picks action randomly (uniform distribution) and store S-A-S'-R tuples.
"""

import pickle
from sumo_rl.agents.agent import Agent
from sumo_rl.observations import ObservationFunction
from sumo_rl.rewards import RewardFunction
from sumo_rl.environment.traffic_signal import TrafficSignal
import typing

State=tuple
Action=int
Reward=float

class DummyAgent(Agent):
  """Dummy Agent class."""

  def __init__(self, id: str,
                     observation_fn: ObservationFunction,
                     reward_fn: RewardFunction,
                     controlled_entities: dict[str, TrafficSignal],
                     state_space,
                     action_space):
    """Initialize Dummy agent."""
    super().__init__(id)
    self.observation_fn: ObservationFunction = observation_fn
    self.reward_fn: RewardFunction = reward_fn
    self.controlled_entities = controlled_entities
    self.state_space = state_space
    self.action_space = action_space
    self.history: list[tuple[State, Action, State, Reward]] = []

    self.previous_states: dict = {}
    self.current_states: dict = {}
    self.previous_actions: dict = {}
    self.current_actions: dict = {}

  def reset(self):
    self.previous_states = {}
    self.current_states = {}
    self.previous_actions = {}
    self.current_actions = {}

  def hard_reset(self):
    self.reset()

  def observe(self, observations: dict[str, typing.Any]):
    self.previous_states = self.current_states
    self.current_states = {ID: observations[ID] for ID in self.controlled_entities.keys()}

  def act(self) -> dict[str, int]:
    """Choose action randomly (uniform distribution)."""
    actions = {}
    for ID in self.controlled_entities.keys():
      action = self.action_space.sample()
      actions[ID] = action
    self.previous_actions = actions
    return actions

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

  def can_learn(self) -> bool:
    """True if learning is supported
    """
    return True

  def can_observe(self) -> bool:
    """True if observing is supported
    """
    return True
