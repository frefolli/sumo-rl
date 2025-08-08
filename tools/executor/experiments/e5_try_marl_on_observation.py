from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E5TryMarlOnObservation(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E5", "TryMarlOnObservation", archive)
    self.observations = ['d', 'sv', 'svp', 'svs', 'svd', 'svq']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['dql']
    self.self_adaptives = [False]
