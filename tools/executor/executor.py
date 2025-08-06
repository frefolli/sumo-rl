from tools.executor.archive import Archive
from tools.executor.experiment import Experiment
from tools.executor.experiments import *
import argparse

class Executor:
  def __init__(self) -> None:
    self.archive = Archive()
    self.experiments: dict[str, Experiment] = {exp.id:exp for exp in [
      E0FindBestRewardFunction(self.archive),
      E1FindBestObservationFunction(self.archive),
      E2FindBestDataset(self.archive)
    ]}

  def apply(self, argv: list[str]):
    argument_parser = argparse.ArgumentParser('tools.executor', description='Glorious executor of experiments')
    argument_parser.add_argument('-e', '--experiment', type=str, help='Experiment ID')
    argument_parser.add_argument('-l', '--list-experiments', action='store_true', help='List all available experiments')
    args = argument_parser.parse_args(argv)

    print('Available experiments:')
    if args.list_experiments:
      for exp_id, exp in self.experiments.items():
        print('-', exp_id, ':', exp.name)

    if args.experiment:
      if args.experiment not in self.experiments:
        raise ValueError('Experiment \'%s\' is not known' % args.experiment)
      experiment = self.experiments[args.experiment]
      experiment.all()
