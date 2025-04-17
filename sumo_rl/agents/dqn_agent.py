"""Deep Q-learning Agent class."""

import numpy
from sumo_rl.agents.agent import Agent
from sumo_rl.observations import ObservationFunction
from sumo_rl.rewards import RewardFunction
from sumo_rl.agents.dummy_env import DummyEnv
from sumo_rl.environment.traffic_signal import TrafficSignal
from stable_baselines3.common import utils
import typing

from stable_baselines3 import DQN
from stable_baselines3.common.buffers import ReplayBuffer

class DQNAgent(Agent):
  """Deep Q-learning Agent class."""

  def __init__(self, id: str,
                     observation_fn: ObservationFunction,
                     reward_fn: RewardFunction,
                     controlled_entities: dict[str, TrafficSignal],
                     state_space,
                     action_space):
    """Initialize Q-learning agent."""
    super().__init__(id)
    self.observation_fn: ObservationFunction = observation_fn
    self.reward_fn: RewardFunction = reward_fn
    self.controlled_entities = controlled_entities
    self.state_space = state_space
    self.action_space = action_space

    self.previous_states: dict = {}
    self.current_states: dict = {}
    self.previous_actions: dict = {}
    self.current_actions: dict = {}

    self.dummy_env = DummyEnv(state_space, action_space)
    self.model: DQN = DQN('MlpPolicy', self.dummy_env, verbose=1, device='cpu', buffer_size=512, policy_kwargs=dict(net_arch=[32, 32]))
    self.model._logger = utils.configure_logger(self.model.verbose, self.model.tensorboard_log, '', False)


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
    """Choose action via DQN Model for each entity"""
    actions = {}
    for ID in self.controlled_entities.keys():
      state = self.current_states[ID]
      action, _ = self.model.predict(state)
      actions[ID] = action
    self.previous_actions = actions
    return {k:int(v) for k,v in actions.items()}

  def learn(self, rewards: dict[str, typing.Any]):
    """Update Q-table with new experience."""
    for ID in self.controlled_entities.keys():
      previous_state = self.previous_states[ID]
      current_state = self.current_states[ID]
      previous_action = self.previous_actions[ID]
      reward = rewards[ID]
      self.model.replay_buffer.add(previous_state, current_state, previous_action, reward, numpy.array([False]), [{}])
    #if self.model.replay_buffer.full:
    self.model.train(1, batch_size=1)
    self.model.replay_buffer.reset()

  def serialize(self, output_filepath: str) -> None:
    """Serialize Agent "memory" into an output file
    """
    self.model.save(output_filepath)

  def deserialize(self, input_filepath: str) -> None:
    """Deserialize Agent "memory" from an input file
    """
    self.model.load(input_filepath, env=self.dummy_env)

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
