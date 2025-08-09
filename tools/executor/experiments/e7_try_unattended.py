from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E7TryUnattended(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E7", "TryUnattended", archive, skip_training=True, skip_evaluation=False)
    self.agents = ['fixed15']
    self.shutdowns = [True]
