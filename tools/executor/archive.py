from __future__ import annotations
import os
from typing import Generator
from sumo_rl.models.commons import ensure_dir
from sumo_rl.util.cmd import *
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

class Configuration(sumo_rl.models.serde.SerdeYamlFile):
  def __init__(self,
               agent: str,
               partition: str,
               observation: str,
               reward: str,
               self_adaptive: bool,
               dataset: str,
               shutdown: bool,
               quantization: int,
               tm_alpha: float,
               tm_gamma: float,
               eg_epsilon: float,
               eg_decay: float,
               eg_minimum: float,
               nn_deterministic: bool,
               nn_buffer_size: int,
               nn_entropy_coefficient: float) -> None:
    self.agent: str = agent
    self.partition: str = partition
    self.observation: str = observation
    self.reward: str = reward
    self.self_adaptive: bool = self_adaptive
    self.dataset: str = dataset
    self.shutdown: bool = shutdown
    self.quantization: int = quantization
    self.tm_alpha: float = tm_alpha
    self.tm_gamma: float = tm_gamma
    self.eg_epsilon: float = eg_epsilon
    self.eg_decay: float = eg_decay
    self.eg_minimum: float = eg_minimum
    self.nn_deterministic: bool = nn_deterministic
    self.nn_buffer_size: int = nn_buffer_size
    self.nn_entropy_coefficient: float = nn_entropy_coefficient

  @staticmethod
  def Default() -> Configuration:
    return Configuration(agent='ql',
                         partition='mono',
                         observation='default',
                         reward='dwt',
                         self_adaptive=False,
                         dataset='1',
                         shutdown=False,
                         quantization=16,
                         tm_alpha=0.1,
                         tm_gamma=0.9,
                         eg_epsilon=1.0,
                         eg_decay=0.99,
                         eg_minimum=0.05,
                         nn_deterministic=False,
                         nn_buffer_size=2048,
                         nn_entropy_coefficient=0.0)

  def to_cli(self) -> list[str]:
    args = []
    args += [
      '-A', self.agent,
      '-P', self.partition,
      '-O', self.observation,
      '-R', self.reward,
      '-Ta', str(self.tm_alpha),
      '-Tg', str(self.tm_gamma),
      '-Ee', str(self.eg_epsilon),
      '-Ed', str(self.eg_decay),
      '-Em', str(self.eg_minimum),
      '-Nb', str(self.nn_buffer_size),
      '-Ne', str(self.nn_entropy_coefficient)
    ]
    assert self.self_adaptive in [True, False]
    if self.self_adaptive:
      args.append('-sa')
    if self.shutdown:
      args.append('-stl')
    if self.nn_deterministic:
      args.append('-Nd')
    if self.quantization == 0:
      args.append('-nq')
    else:
      args.append('-ql')
      args.append(str(self.quantization))
    return args

  def trainable(self) -> bool:
    return self.shutdown == False and self.agent not in ['fixed15', 'fixed30', 'fixed45', 'fixed60']

  def hash(self) -> str:
    return '-'.join([
      self.agent,
      self.partition,
      self.observation,
      self.reward,
      ('sa' if self.self_adaptive else 'nsa'),
      self.dataset,
      ('off' if self.shutdown else 'on'),
      (('q%s' % self.quantization) if (self.quantization != 0) else 'nq'),
      ('det' if self.nn_deterministic else 'ndet'),
      ('ta%s' % self.tm_alpha),
      ('tg%s' % self.tm_gamma),
      ('ee%s' % self.eg_epsilon),
      ('ed%s' % self.eg_decay),
      ('em%s' % self.eg_minimum),
      ('nb%s' % self.nn_buffer_size),
      ('ne%s' % self.nn_entropy_coefficient)
    ])

  def to_dict(self) -> dict:
    return {
      'agent': self.agent,
      'partition': self.partition,
      'observation': self.observation,
      'reward': self.reward,
      'self_adaptive': self.self_adaptive,
      'dataset': self.dataset,
      'shutdown': self.shutdown,
      'quantization': self.quantization,
      'tm_alpha': self.tm_alpha,
      'tm_gamma': self.tm_gamma,
      'eg_epsilon': self.eg_epsilon,
      'eg_decay': self.eg_decay,
      'eg_minimum': self.eg_minimum,
      'nn_deterministic': self.nn_deterministic,
      'nn_buffer_size': self.nn_buffer_size,
      'nn_entropy_coefficient': self.nn_entropy_coefficient
    }

  @staticmethod
  def from_dict(data: dict) -> Configuration:
    return Configuration(agent=data['agent'],
                         partition=data['partition'],
                         observation=data['observation'],
                         reward=data['reward'],
                         self_adaptive=data['self_adaptive'],
                         dataset=data['dataset'],
                         shutdown=data['shutdown'],
                         quantization=data['quantization'],
                         tm_alpha=data['tm_alpha'],
                         tm_gamma=data['tm_gamma'],
                         eg_epsilon=data['eg_epsilon'],
                         eg_decay=data['eg_decay'],
                         eg_minimum=data['eg_minimum'],
                         nn_deterministic=data['nn_deterministic'],
                         nn_buffer_size=data['nn_buffer_size'],
                         nn_entropy_coefficient=data['nn_entropy_coefficient'])

  @staticmethod
  def Patch(config: Configuration,
            agent: str|None = None,
            partition: str|None = None,
            observation: str|None = None,
            reward: str|None = None,
            self_adaptive: bool|None = None,
            dataset: str|None = None,
            shutdown: bool|None = None,
            quantization: int|None = None,
            tm_alpha: float|None = None,
            tm_gamma: float|None = None,
            eg_epsilon: float|None = None,
            eg_decay: float|None = None,
            eg_minimum: float|None = None,
            nn_deterministic: bool|None = None,
            nn_buffer_size: int|None = None,
            nn_entropy_coefficient: float|None = None) -> Configuration:
    if self_adaptive is None:
      self_adaptive = config.self_adaptive
    if shutdown is None:
      shutdown = config.shutdown
    if nn_deterministic is None:
      nn_deterministic = config.nn_deterministic
    return Configuration(agent=(agent or config.agent),
                         partition=(partition or config.partition),
                         observation=(observation or config.observation),
                         reward=(reward or config.reward),
                         self_adaptive=self_adaptive,
                         dataset=(dataset or config.dataset),
                         shutdown=shutdown,
                         quantization=(quantization or config.quantization),
                         tm_alpha=(tm_alpha or config.tm_alpha),
                         tm_gamma=(tm_gamma or config.tm_gamma),
                         eg_epsilon=(eg_epsilon or config.eg_epsilon),
                         eg_decay=(eg_decay or config.eg_decay),
                         eg_minimum=(eg_minimum or config.eg_minimum),
                         nn_deterministic=nn_deterministic,
                         nn_buffer_size=(nn_buffer_size or config.nn_buffer_size),
                         nn_entropy_coefficient=(nn_entropy_coefficient or config.nn_entropy_coefficient))

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
    scenario = 'celoria'
    exec_cmd(f'rm -rf ./scenarios/{scenario}/training')
    exec_cmd(f'rm -rf ./scenarios/{scenario}/evaluation')
    training = os.path.abspath(f'./datasets/{id}/training')
    evaluation = os.path.abspath(f'./datasets/{id}/evaluation')
    exec_cmd(f'ln -sf {training} ./scenarios/{scenario}/training')
    exec_cmd(f'ln -sf {evaluation} ./scenarios/{scenario}/evaluation')

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
