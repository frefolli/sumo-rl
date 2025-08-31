import os
import sys
import argparse

from .rounds import Rounds
from .leaderboard import Leaderboard
from .plotter import Plotter
from .barrer import Barrer
from .radarer import  Radarer
from .tabler import Tabler

if __name__ == '__main__':
  metrics = {
    'arrival_rate_mean': True,
    'departure_rate_mean': True,
    'speed_mean': True,
    'speed_var': False,
    'accumulated_waiting_time_mean': False,
    'waiting_time_mean': False,
    'accumulated_waiting_time_var': False,
    'waiting_time_var': False,
  }
  argument_parser = argparse.ArgumentParser('tools.executor', description='Glorious executor of experiments')
  argument_parser.add_argument('-e', '--experiment', type=str, help='Experiment ID')
  args = argument_parser.parse_args(sys.argv[1:])
  exp_id = (args.experiment or 'E0')
  basedir = './experiments/%s' % exp_id

  rounds = Rounds.load(exp_id)
  Plotter.create(os.path.join(basedir, 'plots'), rounds, metrics, mean=False)
  Barrer.create(os.path.join(basedir, 'bars'), rounds, metrics)
  Leaderboard.create(os.path.join(basedir, 'leaderboards'), rounds, metrics)
  Tabler.create(os.path.join(basedir, 'tables'), rounds, metrics)

  metrics = {
    'arrival_rate_mean': True,
    'departure_rate_mean': True,
    'speed_mean': True,
    #'speed_var': False,
    'accumulated_waiting_time_mean': False,
    'waiting_time_mean': False,
    #'accumulated_waiting_time_var': False,
    #'waiting_time_var': False,
  }
  Radarer.create(os.path.join(basedir, 'radars'), rounds, metrics)
