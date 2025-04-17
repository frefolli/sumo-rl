"""Observation functions for traffic signals."""

from sumo_rl.environment.datastore import Datastore
from sumo_rl.observations import ObservationFunction
import sumo_rl.environment.traffic_signal
import sumo_rl.preprocessing.graphs

class SharedVisionObservationFunction(ObservationFunction):
  """SharedVision observation function for traffic signals."""

  def __init__(self,
               me_observation: ObservationFunction,
               you_observation: ObservationFunction,
               vision_graph: sumo_rl.preprocessing.graphs.Graph|None = None):
    """Initialize sharedVision observation function."""
    super().__init__("sharedVision")
    self.me_observation = me_observation
    self.you_observation = you_observation
    self.vision_graph: sumo_rl.preprocessing.graphs.Graph = (vision_graph or sumo_rl.preprocessing.graphs.Graph())

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
    """Return the sharedVision observation."""
    observation = self.me_observation(datastore, ts)
    for you_id in (self.vision_graph.edges.get(ts.id) or []):
      observation += self.you_observation(datastore, self.vision_graph.nodes[you_id])
    return observation


  def observation_space_size(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> int:
    """Subclasses must override this method."""
    total_size = self.me_observation.observation_space_size(ts)
    for you_id in (self.vision_graph.edges.get(ts.id) or []):
      total_size += self.you_observation.observation_space_size(self.vision_graph.nodes[you_id])
    return total_size

  def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
    return "OS%s-%s-%sSO" % (self.name, ts.num_green_phases, len(ts.lanes))
