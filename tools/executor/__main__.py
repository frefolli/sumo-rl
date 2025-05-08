from __future__ import annotations
import os
from typing import Generator
from sumo_rl.models.commons import ensure_dir
import sumo_rl.models.serde

def use_iterations(min: int, max: int = None) -> Generator[int, None, None]:
  if max is None:
    max = min
    min = 0
  for i in range(min, max):
    if i != min:
      print(':: ITERATION END   ', str(i - 1).ljust(3), '::')
    print(':: ITERATION BEGIN ', str(i).ljust(3), '::')
    yield i
  print(':: ITERATION END   ', str(max - 1).ljust(3), '::')
  return None

def spd_say(msg: str):
  if os.path.exists('/usr/bin/spd-say'):
    os.system('spd-say -w -l it "%s"' % msg)
  else:
    print(msg)

def on_event_succed():
  spd_say("Il treno regionale veloce 24 77, di Trenitalia Tper, proveniente da Milano Centrale e diretto a Rimini, via Ravenna, delle ore 18 e 22, è in arrivo al binario 11.")

def on_event_fail():
  spd_say("Il treno regionale veloce 24 77, di Trenitalia Tper, proveniente da Milano Centrale e diretto a Rimini, via Ravenna, previsto in partenza alle ore 18 e 22, oggi non sarà effettuato. Per un guasto, al treno.")

def on_event_S9():
  spd_say("Il treno suburbano S9, 24 9 62 di Trenord, proveniente da Albairate-Vermezzo e diretto a Saronno, delle ore 12:56, è in arrivo al binario 2, invece che al binario 4. Attenzione! allontanarsi dalla linea gialla! Ferma in tutte le stazione eccetto: Cesano Maderno parco delle groane, Ceriano Laghetto parco delle groane.")

def exec_cmd(cmd: str) -> None:
  print('CMD:', cmd)
  if os.system(cmd) != 0:
    on_event_fail()
    raise ValueError(cmd)

class Configuration(sumo_rl.models.serde.SerdeYamlFile):
  def __init__(self, agent: str, partition: str, observation: str, reward: str, self_adaptive: bool, dataset: str) -> None:
    self.agent: str = agent
    self.partition: str = partition
    self.observation: str = observation
    self.reward: str = reward
    self.self_adaptive: bool = self_adaptive
    self.dataset: str = dataset

  @staticmethod
  def Default() -> Configuration:
    return Configuration(agent='ql',
                         partition='mono',
                         observation='default',
                         reward='dwt',
                         self_adaptive=False,
                         dataset='1')

  def to_cli(self) -> list[str]:
    args = []
    args += [
      '-A', self.agent,
      '-P', self.partition,
      '-O', self.observation,
      '-R', self.reward
    ]
    return args

  def hash(self) -> str:
    return '-'.join([
      self.agent,
      self.partition,
      self.observation,
      self.reward,
      ('sa' if self.self_adaptive else 'nsa'),
      self.dataset
    ])

  def to_dict(self) -> dict:
    return {
      'agent': self.agent,
      'partition': self.partition,
      'observation': self.observation,
      'reward': self.reward,
      'self_adaptive': self.self_adaptive,
      'dataset': self.dataset
    }

  @staticmethod
  def from_dict(data: dict) -> Configuration:
    return Configuration(agent=data['agent'],
                         partition=data['partition'],
                         observation=data['observation'],
                         reward=data['reward'],
                         self_adaptive=data['self_adaptive'],
                         dataset=data['dataset'])

  @staticmethod
  def Patch(config: Configuration, agent: str|None = None, partition: str|None = None, observation: str|None = None, reward: str|None = None, self_adaptive: bool|None = None, dataset: str|None = None) -> Configuration:
    if self_adaptive is None:
      self_adaptive = config.self_adaptive
    return Configuration(agent=(agent or config.agent),
                         partition=(partition or config.partition),
                         observation=(observation or config.observation),
                         reward=(reward or config.reward),
                         self_adaptive=self_adaptive,
                         dataset=(dataset or config.dataset))

class Archive:
  def __init__(self) -> None:
    self.path = './archive'
    self.config: Configuration
    self._read_config()

  def _read_config(self):
    file = self.current_config_file()
    if os.path.exists(file):
      self.config = Configuration.from_yaml_file(file)
      return
    self.config = Configuration.Default()
    self._write_config()

  def _write_config(self):
    self.config.to_yaml_file(self.current_config_file())

  def use_dataset(self, id: int):
    exec_cmd('rm -rf ./scenarios/breda/training')
    exec_cmd('rm -rf ./scenarios/breda/evaluation')
    training = os.path.abspath(f'./datasets/{id}/training')
    evaluation = os.path.abspath(f'./datasets/{id}/evaluation')
    exec_cmd(f'ln -sf {training} ./scenarios/breda/training')
    exec_cmd(f'ln -sf {evaluation} ./scenarios/breda/evaluation')

  def switch(self, config: Configuration):
    current_config_dir = os.path.abspath(self.config_dir(self.config))
    next_config_dir = os.path.abspath(self.config_dir(config))
    ensure_dir(current_config_dir)
    ensure_dir(next_config_dir)
    if os.path.exists("outputs"):
      exec_cmd("rm outputs")
    exec_cmd("ln -sf %s outputs" % (next_config_dir,))
    self.use_dataset(config.dataset)

    self.config = config
    self._write_config()

  def current_config_file(self) -> str:
    file = os.path.join(self.path, 'config.yml')
    dir = os.path.dirname(file)
    ensure_dir(dir)
    return file

  def config_dir(self, config: Configuration) -> str:
    dir = os.path.join(self.path, config.hash())
    ensure_dir(dir)
    return dir

def experiment_0_evaluation(archive: Archive):
  ensure_dir('experiments/0/rounds')
  REWARDS = ['dwt', 'p', 'as', 'ql']
  archive.switch(Configuration(agent='ql', observation='default', reward='dwt', partition='mono', self_adaptive=False, dataset='0'))
  for i in use_iterations(5):
    for reward in REWARDS:
      archive.switch(Configuration.Patch(archive.config, reward=reward))
      args = ['python', '-m', 'main', '-r', '-DE']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/0/rounds/%s.csv' % i)

def experiment_0_training(archive: Archive):
  ensure_dir('experiments/0/rounds')
  REWARDS = ['dwt', 'p', 'as', 'ql']
  archive.switch(Configuration(agent='ql', observation='default', reward='dwt', partition='mono', self_adaptive=False, dataset='0'))
  for _ in use_iterations(1):
    for reward in REWARDS:
      archive.switch(Configuration.Patch(archive.config, reward=reward))
      args = ['python', '-m', 'main', '-r', '-DT']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_1_evaluation(archive: Archive):
  ensure_dir('experiments/1/rounds')
  AGENTS = ['fixed', 'ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/1/rounds/%s.csv' % i)

def experiment_1_training(archive: Archive):
  AGENTS = ['ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_2_evaluation(archive: Archive):
  ensure_dir('experiments/2/rounds')
  AGENTS = ['fixed', 'ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/2/rounds/%s.csv' % i)

def experiment_2_training(archive: Archive):
  archive = Archive()
  AGENTS = ['ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_3_evaluation(archive: Archive):
  ensure_dir('experiments/3/rounds')
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/3/rounds/%s.csv' % i)

def experiment_3_training(archive: Archive):
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_4_evaluation(archive: Archive):
  ensure_dir('experiments/4/rounds')
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for sa in [False, True]:
      archive.switch(Configuration.Patch(archive.config, self_adaptive=sa))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      if archive.config.self_adaptive:
        args += ['-sa']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/4/rounds/%s.csv' % i)

def experiment_4_training(archive: Archive):
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for sa in [False, True]:
      archive.switch(Configuration.Patch(archive.config, self_adaptive=sa))
      args = ['python', '-m', 'main', '-r', '-DT', '-sa']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_5_evaluation(archive: Archive):
  ensure_dir('experiments/5/rounds')
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/5/rounds/%s.csv' % i)

def experiment_5_training(archive: Archive):
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_6_evaluation(archive: Archive):
  ensure_dir('experiments/6/rounds')
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for sa in [False, True]:
      archive.switch(Configuration.Patch(archive.config, self_adaptive=sa))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      if archive.config.self_adaptive:
        args += ['-sa']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/6/rounds/%s.csv' % i)

def experiment_6_training(archive: Archive):
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for sa in [False, True]:
      archive.switch(Configuration.Patch(archive.config, self_adaptive=sa))
      args = ['python', '-m', 'main', '-r', '-DT', '-sa']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_7_evaluation(archive: Archive):
  ensure_dir('experiments/7/rounds')
  AGENTS = ['ql', 'fixed', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DE', '-de']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot3')
      exec_cmd('python -m tools.score2')
    exec_cmd('python -m tools.comparer2')
    exec_cmd('mv scores.yml experiments/7/rounds/%s.yml' % i)

def experiment_7_training(archive: Archive):
  AGENTS = ['ql', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))

def experiment_8_evaluation(archive: Archive):
  ensure_dir('experiments/8/rounds')
  REWS = ['ql', 'svdwt', 'svp', 'svas', 'svql']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for rew in REWS:
      archive.switch(Configuration.Patch(archive.config, reward=rew))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/8/rounds/%s.csv' % i)

def experiment_8_training(archive: Archive):
  REWS = ['ql', 'svdwt', 'svp', 'svas', 'svql']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for rew in REWS:
      archive.switch(Configuration.Patch(archive.config, reward=rew))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_9_evaluation(archive: Archive):
  ensure_dir('experiments/9/rounds')
  REWS = ['ql', 'svdwt', 'svp', 'svas', 'svql']
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for i in use_iterations(5):
    for rew in REWS:
      archive.switch(Configuration.Patch(archive.config, reward=rew))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/9/rounds/%s.csv' % i)

def experiment_9_training(archive: Archive):
  REWS = ['ql', 'svdwt', 'svp', 'svas', 'svql']
  archive.switch(Configuration(agent='ppo', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'))
  for _ in use_iterations(2):
    for rew in REWS:
      archive.switch(Configuration.Patch(archive.config, reward=rew))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_10_evaluation(archive: Archive):
  ensure_dir('experiments/10/rounds')
  models = [
      Configuration(agent='fixed', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'),
      Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'),
      Configuration(agent='ppo', observation='svd', reward='svql', partition='mono', self_adaptive=False, dataset='1'),
  ]
  for i in use_iterations(10):
    for model in models:
      archive.switch(model)
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/10/rounds/%s.csv' % i)

def experiment_10_training(archive: Archive):
  models = [
      Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='1'),
      Configuration(agent='ppo', observation='svd', reward='svql', partition='mono', self_adaptive=False, dataset='1'),
  ]
  for _ in use_iterations(2):
    for model in models:
      archive.switch(model)
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_11_evaluation(archive: Archive):
  ensure_dir('experiments/11/rounds')
  models = [
    Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='2'),
    Configuration(agent='ppo', observation='svd', reward='svql', partition='mono', self_adaptive=False, dataset='2')
  ]
  for i in use_iterations(10):
    for model in models:
      archive.switch(model)
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/11/rounds/%s.csv' % i)

def experiment_11_training(archive: Archive):
  models = [
    Configuration(agent='ql', observation='default', reward='ql', partition='mono', self_adaptive=False, dataset='2'),
    Configuration(agent='ppo', observation='svd', reward='svql', partition='mono', self_adaptive=False, dataset='2')
  ]
  for _ in use_iterations(1):
    for model in models:
      archive.switch(model)
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')

def experiment_0():
  archive = Archive()
  experiment_0_training(archive)
  experiment_0_evaluation(archive)

def experiment_1():
  archive = Archive()
  experiment_1_training(archive)
  experiment_1_evaluation(archive)

def experiment_2():
  archive = Archive()
  experiment_2_training(archive)
  experiment_2_evaluation(archive)

def experiment_3():
  archive = Archive()
  experiment_3_training(archive)
  experiment_3_evaluation(archive)

def experiment_4():
  archive = Archive()
  experiment_4_training(archive)
  experiment_4_evaluation(archive)

def experiment_5():
  archive = Archive()
  experiment_5_training(archive)
  experiment_5_evaluation(archive)

def experiment_6():
  archive = Archive()
  experiment_6_training(archive)
  experiment_6_evaluation(archive)

def experiment_7():
  archive = Archive()
  experiment_7_training(archive)
  experiment_7_evaluation(archive)

def experiment_8():
  archive = Archive()
  experiment_8_training(archive)
  experiment_8_evaluation(archive)

def experiment_9():
  archive = Archive()
  experiment_9_training(archive)
  experiment_9_evaluation(archive)

def experiment_10():
  archive = Archive()
  experiment_10_training(archive)
  experiment_10_evaluation(archive)

def experiment_11():
  archive = Archive()
  experiment_11_training(archive)
  experiment_11_evaluation(archive)

def main():
  experiment_10()
  on_event_succed()

if __name__ == '__main__':
  main()
