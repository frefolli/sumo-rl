"""Reward functions for traffic signals."""

import sumo_rl.environment.traffic_signal
from sumo_rl.rewards import RewardFunction
from sumo_rl.environment.datastore import Datastore
import sumo_rl.preprocessing.graphs

class SharedVisionRewardFunction(RewardFunction):
  """Shared Vision reward function for traffic signals."""

  def __init__(self,
               reward_function: RewardFunction,
               vision_graph: sumo_rl.preprocessing.graphs.Graph|None = None):
    """Initialize queue length reward function."""
    super().__init__("sharedVision")
    self.reward_function: RewardFunction = reward_function
    self.vision_graph: sumo_rl.preprocessing.graphs.Graph = (vision_graph or sumo_rl.preprocessing.graphs.Graph())

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> float:
    """Return the shared reward"""
    reward = self.reward_function.cache(datastore, ts)
    for you_id in (self.vision_graph.edges.get(ts.id) or []):
      reward += self.reward_function.cache(datastore, self.vision_graph.nodes[you_id])
    return reward
