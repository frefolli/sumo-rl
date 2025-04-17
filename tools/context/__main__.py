import argparse
import os
import sys

def exec_cmd(cmd: str) -> None:
  assert os.system(cmd) == 0

def switch_experiment(experiment_name: str) -> None:
  experiment_training = 'experiments/%s/training' % experiment_name
  experiment_evaluation = 'experiments/%s/evaluation' % experiment_name
  scenario_training = 'scenarios/breda/training'
  scenario_evaluation = 'scenarios/breda/evaluation'
  exec_cmd('rm -rf %s' % (scenario_training,))
  exec_cmd('rm -rf %s' % (scenario_evaluation,))
  exec_cmd('cp -r %s %s' % (experiment_training, scenario_training))
  exec_cmd('cp -r %s %s' % (experiment_evaluation, scenario_evaluation))

def main():
  argument_parser = argparse.ArgumentParser(description='Context switch utility')
  argument_parser.add_argument('-E', '--experiment', type=str, help='Switches between experiments')
  cli_args = argument_parser.parse_args(sys.argv[1:])

  if cli_args.experiment:
    switch_experiment(cli_args.experiment)

if __name__ == "__main__":
  main()
