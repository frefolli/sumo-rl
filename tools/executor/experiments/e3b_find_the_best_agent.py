from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E3BFindBestAgent(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E3B", "FindBestAgent", archive)
    self.observations = ['s']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily']
    self.agents = ['ppo', 'dqn']
