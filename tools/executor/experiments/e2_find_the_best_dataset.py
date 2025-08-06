from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E2FindBestDataset(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E2", "FindBestDataset", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily', 'curriculum_daily_plus_disruption', 'frankestein']
