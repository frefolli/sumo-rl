"""Observation functions for traffic signals."""

from sumo_rl.environment.datastore import Datastore
from sumo_rl.observations import ObservationFunction
import sumo_rl.environment.traffic_signal
import numpy

class PhaseObservationFunction(ObservationFunction):
  """Phase observation function for traffic signals."""

  def __init__(self):
    """Initialize phase observation function."""
    super().__init__("phase")

  # def encode(self, state: numpy.ndarray, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
  #   """Encode the state of the traffic signal into a hashable object."""
  #   phase = int(numpy.where(state[: ts.num_green_phases] == 1)[0])
  #   # tuples are hashable and can be used as key in python dictionary
  #   return tuple([phase])

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
    """Return the phase observation."""
    phase_id = [1 if ts.green_phase == i else 0 for i in range(ts.num_green_phases)]  # one-hot encoding
    observation = numpy.array(phase_id, dtype=numpy.float32)
    state = self.encode(observation, ts)
    return state

  def observation_space_size(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> int:
    """Return the observation space."""
    return ts.num_green_phases

  def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
    return "OS%s-%s-%sSO" % (self.name, ts.num_green_phases, len(ts.lanes))
