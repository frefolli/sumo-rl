from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E8TryUnquantized(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E8", "TryUnquantized", archive)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['ppo']
    self.quantizations = [0, 8, 16, 32, 64]
