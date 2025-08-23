from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E11TryTabularDeterminism(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E11", "TryTabularDeterminism", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['dql']
    self.quantizations = [16]
    self.partitions = ['mono']
    self.eg_minimum = [0.05, 0.01, 0.005, 0.001]
