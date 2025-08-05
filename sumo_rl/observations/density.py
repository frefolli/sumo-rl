"""Observation functions for traffic signals."""

from sumo_rl.environment.datastore import Datastore
from sumo_rl.observations import ObservationFunction
import sumo_rl.environment.traffic_signal
import numpy

class DensityObservationFunction(ObservationFunction):
  """Density observation function for traffic signals."""

  def __init__(self):
    """Initialize density observation function."""
    super().__init__("density")

  # def encode(self, state: numpy.ndarray, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
  #   """Encode the state of the traffic signal into a hashable object."""
  #   density = [self.discretize_density(d) for d in state]
  #   # tuples are hashable and can be used as key in python dictionary
  #   return tuple(density)

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
    """Return the density observation."""
    density = [datastore.lanes[lane_ID]['lso'] for lane_ID in ts.lanes]
    observation = numpy.array(density, dtype=numpy.float32)
    state = self.encode(observation, ts)
    return state

  def observation_space_size(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> int:
    """Return the observation space."""
    return len(ts.lanes)

  def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
    return "OS%s-%s-%sSO" % (self.name, ts.num_green_phases, len(ts.lanes))
