"""Reward functions for traffic signals."""

import sumo_rl.environment.traffic_signal
from sumo_rl.rewards import RewardFunction
from sumo_rl.environment.datastore import Datastore
import numpy

class DiffQueueLengthRewardFunction(RewardFunction):
  """Diff Queue length reward function for traffic signals."""

  def __init__(self):
    """Initialize diff queue length reward function."""
    super().__init__("diff-queue-length")

  def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> float:
    """Return the diff queue length reward"""
    queue_length = numpy.mean([datastore.lanes[lane_ID]['lshn'] for lane_ID in ts.lanes])
    reward = ts.last_queue_length - queue_length
    ts.last_queue_length = queue_length
    return reward
