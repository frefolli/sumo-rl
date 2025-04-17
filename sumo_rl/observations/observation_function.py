"""Observation functions for traffic signals."""

import abc
from sumo_rl.environment.datastore import Datastore
import sumo_rl.environment.traffic_signal
import gymnasium.spaces
import numpy
QUANTIZATION_LEVELS=64

class ObservationFunction(abc.ABC):
  """Abstract base class for observation functions."""

  def __init__(self, name: str):
    """Initialize observation function."""
    self.name = name

  @abc.abstractmethod
  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
    """Subclasses must override this method."""
    pass

  def observation_space(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> gymnasium.spaces.Box:
    """Return the observation space."""
    return gymnasium.spaces.Box(low=numpy.zeros(self.observation_space_size(ts), dtype=numpy.float32),
                                high=numpy.ones(self.observation_space_size(ts), dtype=numpy.float32))

  @abc.abstractmethod
  def observation_space_size(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> int:
    """Subclasses must override this method."""
    pass

  @abc.abstractmethod
  def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> str:
    """Subclasses must override this method."""
    pass

  def discretize_density(self, density):
    assert density >= 0
    assert density <= 1
    return int(density * QUANTIZATION_LEVELS) / QUANTIZATION_LEVELS

  def encode(self, state: numpy.ndarray, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
    """Encode the state of the traffic signal into a hashable object."""
    return tuple(map(self.discretize_density, state))
