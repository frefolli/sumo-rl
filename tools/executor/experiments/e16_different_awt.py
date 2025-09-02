from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E16TryDifferentAwt(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E16", "TryDifferentAwt", archive)
    self.rewards = ['dwt', 'awt']
