import subprocess
import os
import time
from tools.executor.archive import Configuration

def exec_cmd(cmd: str) -> int:
  print('>', cmd)
  return os.system(cmd)

class Set:
  def __init__(self, name: str, config: Configuration) -> None:
    self.name = name
    self.config = config

  def select(self):
    self.use_outputs()
    self.use_dataset()

  def use_outputs(self):
    if not os.path.exists('./archive'):
      exec_cmd('mkdir -p ./archive')
    archive_path = os.path.abspath(os.path.join('./archive', self.name))
    if not os.path.exists(archive_path):
      exec_cmd('mkdir -p %s' % archive_path)
    assert 0 == exec_cmd('rm -rf outputs')
    assert 0 == exec_cmd('ln -sf %s outputs' % archive_path)

  def use_dataset(self):
    scenario = 'celoria'
    assert 0 == exec_cmd(f'rm -rf ./scenarios/{scenario}/training')
    assert 0 == exec_cmd(f'rm -rf ./scenarios/{scenario}/evaluation')
    training = os.path.abspath(f'./datasets/{self.config.dataset}/training')
    evaluation = os.path.abspath(f'./datasets/{self.config.dataset}/evaluation')
    assert 0 == exec_cmd(f'ln -sf {training} ./scenarios/{scenario}/training')
    assert 0 == exec_cmd(f'ln -sf {evaluation} ./scenarios/{scenario}/evaluation')

configs = [
  Set('dql-d-dwt-mon', Configuration.Patch(Configuration.Default(), dataset='monolithic', agent='dql', observation='d', reward='dwt')),
  Set('dql-d-dwt-cd', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily', agent='dql', observation='d', reward='dwt')),
  Set('dql-d-dwt', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='dql', observation='d', reward='dwt')),
  Set('dql-svp-svdwt', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='dql', observation='svp', reward='svdwt')),
  Set('ppo-d-dwt', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='ppo', observation='d', reward='dwt')),
  Set('fixed15', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='fixed15', observation='d', reward='dwt')),
  Set('fixed30', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='fixed30', observation='d', reward='dwt')),
  Set('fixed45', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='fixed45', observation='d', reward='dwt')),
  Set('fixed60', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='fixed60', observation='d', reward='dwt')),
  Set('priority', Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', agent='fixed15', observation='d', reward='dwt', shutdown=True)),
]

def train_eval():
  for config in configs:
    config.select()
    args = ' '.join(config.config.to_cli())
    if config.config.trainable():
      good = (0 == exec_cmd('python -m main %s -r -S 170700 -DT' % args))
      assert good
    good = (0 == exec_cmd('python -m main %s -r -S 170701 -DE' % args))
    assert good

def plot():
  for config in configs:
    config.select()
    good = (0 == exec_cmd('python -m tools.plot-global-metrics'))
    assert good

def score():
  for config in configs:
    config.select()
    good = (0 == exec_cmd('python -m tools.extract-global-metrics'))
    assert good

def video():
  for config in configs:
    config.select()
    video_path = os.path.abspath(os.path.join('./video', config.name + '.mp4'))
    assert 0 == exec_cmd('rm -rf %s' % video_path)
    proc = subprocess.Popen(['ffmpeg', '-video_size', '1920x1080', '-framerate', '60', '-f', 'alsa', '-ac', '2', '-f', 'x11grab', '-i', ':0.0', video_path])
    args = ' '.join(config.config.to_cli())
    good = (0 == exec_cmd('python -m main %s -S 170701 -DD -g -Sb 30000' % args))
    proc.terminate()
    assert good

if __name__ == '__main__':
  train_eval()
  #plot()
  #score()
