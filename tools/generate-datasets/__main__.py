from sumo_rl.util.cmd import exec_cmd
import argparse
import sys

class Dataset:
  def __init__(self, id: str, training: list[str], evaluation: list[str]) -> None:
    self.id: str = id
    self.training: list[str] = training
    self.evaluation: list[str] = evaluation

  def generate(self, seed: int, scenario: str) -> None:
    exec_cmd('rm -rf datasets/%s' % self.id)
    exec_cmd('mkdir -p datasets/%s' % self.id)
    exec_cmd('rm -rf training')
    exec_cmd('rm -rf evaluation')
    exec_cmd('python -m tools.generate-flows --scenario %s --seed %s -r traffic-registry.yml -o training %s' % (scenario, seed, ' '.join(self.training)))
    exec_cmd('python -m tools.generate-flows --scenario %s --seed %s -r traffic-registry.yml -o evaluation %s' % (scenario, seed, ' '.join(self.evaluation)))
    exec_cmd('mv training evaluation datasets/%s' % self.id)

if __name__ == '__main__':
  datasets = [
    Dataset(
      'frankestein', [
        '4,100000,£,*,~'
      ], [
        '1,£,N1,N2,N1,N3,N1', '1,£,N1,N4,N1,N5,N1', '1,£,N1,STPL2,N1,STPL3,N1', '1,£,N1,CT2,N1,CT3,N1'
      ]
    ),
    Dataset(
      'curriculum_daily', [
        '2,£,N1,N2,N1,N3,N1', '2,£,N1,N4,N1,N5,N1'
      ], [
        '1,£,N1,N2,N1,N3,N1', '1,£,N1,N4,N1,N5,N1', '1,£,N1,STPL2,N1,STPL3,N1', '1,£,N1,CT2,N1,CT3,N1'
      ]
    ),
    Dataset(
      'curriculum_daily_plus_disruption', [
        '1,£,N1,N2,N1,N3,N1', '1,£,N1,N4,N1,N5,N1', '1,£,N1,ST2,N1,N3,N1', '1,£,N1,N4,N1,CT5,N1'
      ], [
        '1,£,N1,N2,N1,N3,N1', '1,£,N1,N4,N1,N5,N1', '1,£,N1,STPL2,N1,STPL3,N1', '1,£,N1,CT2,N1,CT3,N1'
      ]
    )
  ]

  argument_parser = argparse.ArgumentParser(description='generate datasets')
  argument_parser.add_argument('-S', '--seed', default=None, type=int, help='Input seed')
  argument_parser.add_argument('-s', '--scenario', default='celoria', type=str, help='Input scenario')
  cli_args = argument_parser.parse_args(sys.argv[1:])

  for dataset in datasets:
    dataset.generate(cli_args.seed or 0, cli_args.scenario)
