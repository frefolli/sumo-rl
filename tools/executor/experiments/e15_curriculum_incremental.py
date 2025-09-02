from tools.executor.experiments.combinatorial_experiment import CombinatorialExperiment
from tools.executor.archive import Archive

class E15TryCurriculumIncremental(CombinatorialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E15", "TryCurriculumIncremental", archive)
    self.agents = ['dql']
    self.observations = ['d']
    self.rewards = ['dwt']
    self.partitions = ['mono']
    self.self_adaptives = [False]
    self.shutdowns = [False]
    self.quantizations = [16]
    self.tm_alpha = [0.1]
    self.tm_gamma = [0.9]
    self.eg_epsilon = [1.0]
    self.eg_decay = [0.99]
    self.eg_minimum = [0.05]
    self.nn_deterministic = [False]
    self.nn_buffer_size = [2048]
    self.nn_entropy_coefficient = [0.0]
    self.nn_neural_size = [32]
    self.datasets = ['curriculum_daily_plus_disruption', 'incremental']
