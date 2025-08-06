from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E3CFindBestFixedAgent(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E3C", "FindBestFixedAgent", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily']
    self.agents = ['fixed15', 'fixed30', 'fixed45', 'fixed60']
