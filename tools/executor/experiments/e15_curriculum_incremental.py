from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E15TryCurriculumIncremental(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E15", "TryCurriculumIncremental", archive)
    self.datasets = ['curriculum_daily_plus_disruption', 'incremental']
