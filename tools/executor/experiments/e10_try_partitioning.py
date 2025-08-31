from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E10TryDifferentPartitioningSchemes(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E10", "TryDifferentPartitioningSchemes", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['dql']
    self.quantizations = [16]
    self.partitions = ['mono', 'space']
