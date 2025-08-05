from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E1FindBestObservationFunction(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E1", "FindBestObservationFunction", archive)
    self.observations = ['default', 's', 'd', 'q']
