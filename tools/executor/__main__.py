from __future__ import annotations
import argparse
import os
import sys
from sumo_rl.models.commons import ensure_dir
import sumo_rl.models.serde

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
  def __init__(self, agent: str, partition: str, observation: str, reward: str) -> None:
    self.agent: str = agent
    self.partition: str = partition
    self.observation: str = observation
    self.reward: str = reward

  @staticmethod
  def Default() -> Configuration:
    return Configuration(agent='ql',
                         partition='mono',
                         observation='default',
                         reward='dwt')

  def to_cli(self) -> list[str]:
    return [
      '-A', self.agent,
      '-P', self.partition,
      '-O', self.observation,
      '-R', self.reward
    ]

  def hash(self) -> str:
    return '-'.join([
      self.agent,
      self.partition,
      self.observation,
      self.reward
    ])

  def to_dict(self) -> dict:
    return {
      'agent': self.agent,
      'partition': self.partition,
      'observation': self.observation,
      'reward': self.reward
    }

  @staticmethod
  def from_dict(data: dict) -> Configuration:
    return Configuration(agent=data['agent'],
                         partition=data['partition'],
                         observation=data['observation'],
                         reward=data['reward'])

  @staticmethod
  def Patch(config: Configuration, agent: str|None = None, partition: str|None = None, observation: str|None = None, reward: str|None = None) -> Configuration:
    return Configuration(agent=(agent or config.agent),
                         partition=(partition or config.partition),
                         observation=(observation or config.observation),
                         reward=(reward or config.reward))

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

  def switch(self, config: Configuration):
    current_config_dir = os.path.abspath(self.config_dir(self.config))
    next_config_dir = os.path.abspath(self.config_dir(config))
    ensure_dir(current_config_dir)
    ensure_dir(next_config_dir)
    if os.path.exists("outputs"):
      exec_cmd("rm outputs")
    exec_cmd("ln -sf %s outputs" % (next_config_dir,))

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

def experiment_0():
  archive = Archive()
  REWARDS = ['dwt', 'p', 'as', 'ql']
  archive.switch(Configuration(agent='ql', observation='default', reward='dwt', partition='mono'))
  for reward in REWARDS:
    archive.switch(Configuration.Patch(archive.config, reward=reward))
    args = ['python', '-m', 'main', '-r', '-DE', '-DT']
    args += archive.config.to_cli()
    exec_cmd(' '.join(args))
    exec_cmd('python -m tools.plot2')
    exec_cmd('python -m tools.score')

def experiment_1_evaluation():
  archive = Archive()
  AGENTS = ['fixed', 'ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for i in range(5):
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

def experiment_1_training():
  archive = Archive()
  AGENTS = ['ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for _ in range(2):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DT']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')
      exec_cmd('python -m tools.score')

def experiment_2_evaluation():
  archive = Archive()
  AGENTS = ['fixed', 'ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for i in range(5):
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

def experiment_2_training():
  archive = Archive()
  AGENTS = ['ql', 'dqn', 'ppo']
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for _ in range(2):
    for agent in AGENTS:
      archive.switch(Configuration.Patch(archive.config, agent=agent))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')
      exec_cmd('python -m tools.score')

def experiment_3_evaluation():
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive = Archive()
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for i in range(5):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.score')
    exec_cmd('python -m tools.comparer')
    exec_cmd('mv scores.csv experiments/2/rounds/%s.csv' % i)

def experiment_3_training():
  OBSS = ['default', 'sv', 'svp', 'svd', 'svq']
  archive = Archive()
  archive.switch(Configuration(agent='ql', observation='default', reward='ql', partition='mono'))
  for _ in range(2):
    for obs in OBSS:
      archive.switch(Configuration.Patch(archive.config, observation=obs))
      args = ['python', '-m', 'main', '-r', '-DE']
      if archive.config.agent not in ['fixed', 'ql']:
        args += ['-j', '1']
      args += archive.config.to_cli()
      exec_cmd(' '.join(args))
      exec_cmd('python -m tools.plot2')
      exec_cmd('python -m tools.score')

def main():
  experiment_3_training()
  experiment_3_evaluation()
  on_event_succed()

if __name__ == '__main__':
  main()
