from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E3BFindBestDeepAgent(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E3B", "FindBestDeepAgent", archive, skip_training=True)
    self.observations = ['d']
    self.rewards = ['dwt']
    self.datasets = ['curriculum_daily_plus_disruption']
    self.agents = ['ppo', 'dqn']
