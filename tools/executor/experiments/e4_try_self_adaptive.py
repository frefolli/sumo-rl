from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E4TrySelfAdaptive(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E4", "TrySelfAdaptive", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['dql']
    self.self_adaptives = [False, True]
