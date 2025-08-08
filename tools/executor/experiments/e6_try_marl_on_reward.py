from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E6TryMarlOnReward(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E6", "TryMarlOnReward", archive)
    self.rewards = ['dwt', 'svdwt', 'svp', 'svas', 'svql', 'svdql']
    self.observations = ['d']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['dql']
    self.self_adaptives = [False]
