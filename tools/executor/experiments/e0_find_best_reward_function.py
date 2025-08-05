from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E0FindBestRewardFunction(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E0", "FindBestRewardFunction", archive)
    self.rewards = ['dwt', 'p', 'as', 'ql', 'dql']
