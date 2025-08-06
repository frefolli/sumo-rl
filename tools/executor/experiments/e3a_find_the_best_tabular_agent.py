from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E3AFindBestTabularAgent(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E3A", "FindBestTabularAgent", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['sarsa', 'ql', 'dql']
