"""Observation functions for traffic signals."""

from sumo_rl.environment.datastore import Datastore
from sumo_rl.observations import ObservationFunction
import sumo_rl.environment.traffic_signal
import gymnasium.spaces
import numpy

class DefaultObservationFunction(ObservationFunction):
    """Default observation function for traffic signals."""

    def __init__(self):
        """Initialize default observation function."""
        super().__init__("default")

    def encode(self, state: numpy.ndarray, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
        """Encode the state of the traffic signal into a hashable object."""
        phase = int(numpy.where(state[: ts.num_green_phases] == 1)[0])
        min_green = state[ts.num_green_phases]
        density_queue = [self.discretize_density(d) for d in state[ts.num_green_phases + 1 :]]
        # tuples are hashable and can be used as key in python dictionary
        return tuple([phase, min_green] + density_queue)

    def __call__(self, datastore: Datastore, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> tuple:
        """Return the default observation."""
        phase_id = [1 if ts.green_phase == i else 0 for i in range(ts.num_green_phases)]  # one-hot encoding
        min_green = [0 if ts.time_since_last_phase_change < ts.min_green + ts.yellow_time else 1]
        density = [datastore.lanes[lane_ID]['lso'] for lane_ID in ts.lanes]
        queue = [datastore.lanes[lane_ID]['lso'] * datastore.lanes[lane_ID]['lshn'] / datastore.lanes[lane_ID]['lsvn'] if (datastore.lanes[lane_ID]['lsvn'] != 0.0) else 0.0 for lane_ID in ts.lanes]
        observation = numpy.array(phase_id + min_green + density + queue, dtype=numpy.float32)
        state = self.encode(observation, ts)
        return state

    def observation_space(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal) -> gymnasium.spaces.Box:
        """Return the observation space."""
        return gymnasium.spaces.Box(
            low=numpy.zeros(2 + 2 * len(ts.lanes), dtype=numpy.float32),
            high=numpy.ones(2 + 2 * len(ts.lanes), dtype=numpy.float32),
        )

    def hash(self, ts: sumo_rl.environment.traffic_signal.TrafficSignal):
        return "OS%s-%s-%sSO" % (self.name, ts.num_green_phases, len(ts.lanes))
