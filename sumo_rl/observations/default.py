"""Observation functions for traffic signals."""

from sumo_rl.environment.datastore import Datastore
from sumo_rl.observations import ObservationFunction
import sumo_rl.environment.traffic_signal
import numpy

class DefaultObservationFunction(ObservationFunction):
  """Default observation function for traffic signals."""

  def __init__(self):
    """Initialize default observation function."""
    super().__init__("default")

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
    """Return the default observation."""
    phase_id = [1 if ts.green_phase == i else 0 for i in range(ts.num_green_phases)]  # one-hot encoding
    min_green = [0 if ts.time_since_last_phase_change < ts.min_green + ts.yellow_time else 1]
    density = [datastore.lanes[lane_ID]['lso'] for lane_ID in ts.lanes]
    queue = [datastore.lanes[lane_ID]['lso'] * datastore.lanes[lane_ID]['lshn'] / datastore.lanes[lane_ID]['lsvn'] if (datastore.lanes[lane_ID]['lsvn'] != 0.0) else 0.0 for lane_ID in ts.lanes]
    observation = numpy.array(phase_id + min_green + density + queue, dtype=numpy.float32)
    state = self.encode(observation, ts)
    return state

  def observation_space_size(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> int:
    """Return the observation space."""
    return ts.num_green_phases + 1 + 2 * len(ts.lanes)

  def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
    return "OS%s-%s-%sSO" % (self.name, ts.num_green_phases, len(ts.lanes))
