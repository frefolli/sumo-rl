from tools.executor.archive import Archive
from tools.executor.experiment import Experiment
from tools.executor.experiments import *
import argparse
import random

class Executor:
  def __init__(self) -> None:
    self.archive = Archive()
    self.experiments: dict[str, Experiment] = {exp.id:exp for exp in [
      E0FindBestRewardFunction(self.archive),
      E1FindBestObservationFunction(self.archive),
      E2FindBestDataset(self.archive),
      E3AFindBestTabularAgent(self.archive),
      E3BFindBestDeepAgent(self.archive),
      E3CFindBestFixedAgent(self.archive),
      E4TrySelfAdaptive(self.archive),
      E5TryMarlOnObservation(self.archive),
      E6TryMarlOnReward(self.archive),
      E7TryUnattended(self.archive),
      E8TryUnquantized(self.archive),
      E9TryDifferentQuantizationLevels(self.archive),
      E10TryDifferentPartitioningSchemes(self.archive),
      E11TryTabularDeterminism(self.archive),
      E12TryNeuralBufSize(self.archive),
      E13TryNeuralEntropy(self.archive),
      E14TryNeuralSize(self.archive),
      E15TryCurriculumIncremental(self.archive),
      E16TryDifferentAwt(self.archive),
      DemoTraining(self.archive)
    ]}

  def apply(self, argv: list[str]):
    argument_parser = argparse.ArgumentParser('tools.executor', description='Glorious executor of experiments')
    argument_parser.add_argument('-e', '--experiment', type=str, help='Experiment ID')
    argument_parser.add_argument('-l', '--list-experiments', action='store_true', help='List all available experiments')
    argument_parser.add_argument('-S', '--seed', type=int, default=0, help='Experiment SEED (default 0)')
    args = argument_parser.parse_args(argv)

    print('Available experiments:')
    if args.list_experiments:
      for exp_id, exp in self.experiments.items():
        print('-', exp_id, ':', exp.name)
    random.seed(args.seed)
    if args.experiment:
      if args.experiment not in self.experiments:
        raise ValueError('Experiment \'%s\' is not known' % args.experiment)
      experiment = self.experiments[args.experiment]
      experiment.all()
