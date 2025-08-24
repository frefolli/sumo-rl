from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E12TryNeuralBufSize(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E12", "TryNeuralBufSize", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['ppo']
    self.quantizations = [16]
    self.partitions = ['mono']
    self.nn_deterministic = [False]
    self.nn_buffer_size = [256, 512, 1024, 2048]
