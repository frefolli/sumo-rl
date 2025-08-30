from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E13TryNeuralEntropy(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E13", "TryNeuralEntropy", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['ppo']
    self.quantizations = [16]
    self.partitions = ['mono']
    self.nn_deterministic = [False]
    self.nn_buffer_size = [512]
    self.nn_entropy_coefficient = [0.0, 0.0001, 0.001, 0.01]
