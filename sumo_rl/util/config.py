from __future__ import annotations
from sumo_rl.models.serde import SerdeJsonFile, SerdeYamlFile, SerdeDict
from sumo_rl.models.commons import ensure_dir
import os
import random

def get_all_qualified_paths_with_extension(base_dir: str, files: list[str], ext: str = '.rou.xml') -> list[str]:
  result = []
  for file in files:
    path = os.path.join(base_dir, file)
    if os.path.isdir(path):
      result += get_all_qualified_paths_with_extension(path, os.listdir(path))
    else:
      if path.endswith(ext):
        result.append(path)
      elif path.endswith('order.yml'):
        # it's an order file
        relative_dir = os.path.dirname(path)
        for listed_file in SerdeYamlFile.from_yaml_file(path):
          result.append(os.path.join(relative_dir, listed_file))
  return result
  

class SumoConfig(SerdeDict):
  def __init__(self, data: dict):
    self.seconds: int = data['seconds']
    self.min_green: int = data['min_green']
    self.delta_time: int = data['delta_time']
    self.sumo_seed: int = (data.get('sumo_seed') or random.randint(1, 100000))
    self.further_cmd_args: list[str] = data['further_cmd_args']

  def to_dict(self) -> dict:
    return {
      'seconds': self.seconds,
      'min_green': self.min_green,
      'delta_time': self.delta_time,
      'sumo_seed': self.sumo_seed,
      'further_cmd_args': self.further_cmd_args,
    }

  @staticmethod
  def from_dict(data: dict) -> SumoConfig:
    return SumoConfig(data)

class QLAgentConfig(SerdeDict):
  def __init__(self, data: dict):
    self.alpha: float = data['alpha']
    self.gamma: float = data['gamma']
    self.initial_epsilon: float = data['initial_epsilon']
    self.min_epsilon: float = data['min_epsilon']
    self.decay: int = data['decay']

  def to_dict(self) -> dict:
    return {
      'alpha': self.alpha,
      'gamma': self.gamma,
      'initial_epsilon': self.initial_epsilon,
      'min_epsilon': self.min_epsilon,
      'decay': self.decay,
    }

  @staticmethod
  def from_dict(data: dict) -> QLAgentConfig:
    return QLAgentConfig(data)

class FixedAgentConfig(SerdeDict):
  def __init__(self, data: dict):
    self.cycle_time: int = data['cycle_time']

  def to_dict(self) -> dict:
    return {
      'cycle_time': self.cycle_time,
    }

  @staticmethod
  def from_dict(data: dict) -> FixedAgentConfig:
    return FixedAgentConfig(data)

class AgentsConfig(SerdeDict):
  def __init__(self, data: dict):
    self.ql: QLAgentConfig = QLAgentConfig.from_dict(data['ql'])
    self.fixed: FixedAgentConfig = FixedAgentConfig.from_dict(data['fixed'])

  def to_dict(self) -> dict:
    return {
      'ql': self.ql.to_dict(),
      'fixed': self.fixed.to_dict(),
    }

  @staticmethod
  def from_dict(data: dict) -> AgentsConfig:
    return AgentsConfig(data)

class TrainingConfig(SerdeDict):
  def __init__(self, data: dict):
    self.seconds: int = data['seconds']

  def to_dict(self) -> dict:
    return {
      'seconds': self.seconds,
    }

  @staticmethod
  def from_dict(data: dict) -> TrainingConfig:
    return TrainingConfig(data)

class EvaluationConfig(SerdeDict):
  def __init__(self, data: dict):
    self.seconds: int = data['seconds']

  def to_dict(self) -> dict:
    return {
      'seconds': self.seconds,
    }

  @staticmethod
  def from_dict(data: dict) -> EvaluationConfig:
    return EvaluationConfig(data)

class DemoConfig(SerdeDict):
  def __init__(self, data: dict):
    self.seconds: int = data['seconds']

  def to_dict(self) -> dict:
    return {
      'seconds': self.seconds,
    }

  @staticmethod
  def from_dict(data: dict) -> DemoConfig:
    return DemoConfig(data)

class ScenarioConfig(SerdeYamlFile, SerdeJsonFile):
  def __init__(self, data: dict):
    self._path: str = ""
    self._network: str = data['network']
    self._training_routes: list[str] = data['routes']['training']
    self._evaluation_routes: list[str] = data['routes']['evaluation']
    self._demo_routes: list[str] = data['routes']['demo']
    self.network = ""
    self.training_routes: list[str] = []
    self.evaluation_routes: list[str] = []
    self.demo_routes: list[str] = []

  def set_path(self, path: str):
    self.network = ""
    self.training_routes = []
    self.evaluation_routes = []
    self.demo_routes = []

    network = os.path.join(path, self._network)
    if not os.path.exists(network):
      raise ValueError("scenario %s declared %s network file but %s doesn't exist" % (path, self._network, network))

    training_routes: list[str] = []
    for qualified in get_all_qualified_paths_with_extension(path, self._training_routes, ".rou.xml"):
      if not os.path.exists(qualified):
        raise ValueError("scenario %s declared a training route file but %s doesn't exist" % (path, qualified))
      training_routes.append(qualified)

    evaluation_routes: list[str] = []
    for qualified in get_all_qualified_paths_with_extension(path, self._evaluation_routes, ".rou.xml"):
      if not os.path.exists(qualified):
        raise ValueError("scenario %s declared a evaluation route file but %s doesn't exist" % (path, qualified))
      evaluation_routes.append(qualified)

    demo_routes: list[str] = []
    for qualified in get_all_qualified_paths_with_extension(path, self._demo_routes, ".rou.xml"):
      if not os.path.exists(qualified):
        raise ValueError("scenario %s declared a demo route file but %s doesn't exist" % (path, qualified))
      demo_routes.append(qualified)
    
    self._path = path
    self.network = network
    self.training_routes = training_routes
    self.evaluation_routes = evaluation_routes
    self.demo_routes = demo_routes

  def get_path(self) -> str:
    if self._path == "":
      raise ValueError("path not set in ScenarioConfig")
    return self._path

  def to_dict(self) -> dict:
    return {
      'network': self._network,
      'routes': {
        'training': self._training_routes,
        'evaluation': self._evaluation_routes,
        'demo': self._demo_routes,
      },
    }

  @staticmethod
  def from_dict(data: dict) -> ScenarioConfig:
    return ScenarioConfig(data)

class ArtifactsConfig(SerdeDict):
  def __init__(self, data: dict):
    self.agents: str = data['agents']
    self.metrics: str = data['metrics']
    self.plots: str = data['plots']

  def to_dict(self) -> dict:
    return {
      'agents': self.agents,
      'metrics': self.metrics,
      'plots': self.plots,
    }

  @staticmethod
  def from_dict(data: dict) -> ArtifactsConfig:
    return ArtifactsConfig(data)

class Config(SerdeYamlFile, SerdeJsonFile):
  def __init__(self, data: dict):
    self.sumo: SumoConfig = SumoConfig.from_dict(data['sumo'])
    self.agents: AgentsConfig = AgentsConfig.from_dict(data['agents'])
    self.training: TrainingConfig = TrainingConfig.from_dict(data['training'])
    self.evaluation: EvaluationConfig = EvaluationConfig.from_dict(data['evaluation'])
    self.demo: DemoConfig = DemoConfig.from_dict(data['demo'])
    self.artifacts: ArtifactsConfig = ArtifactsConfig.from_dict(data['artifacts'])

    path = data['scenario']
    self.scenario: ScenarioConfig = ScenarioConfig.from_yaml_file(os.path.join(path, 'config.yml'))
    self.scenario.set_path(path)

  def to_dict(self) -> dict:
    return {
      'sumo': self.sumo.to_dict(),
      'agents': self.agents.to_dict(),
      'training': self.training.to_dict(),
      'evaluation': self.evaluation.to_dict(),
      'demo': self.demo.to_dict(),
      'scenario': self.scenario.get_path(),
      'artifacts': self.artifacts.to_dict(),
    }

  @staticmethod
  def from_dict(data: dict) -> Config:
    return Config(data)

  def __repr__(self) -> str:
    return self.to_yaml()

  def agents_dir(self, episode: int|None) -> str:
    if episode is None:
      return ensure_dir("%s/final" % (self.artifacts.agents))
    return ensure_dir("%s/%s" % (self.artifacts.agents, episode))

  def agents_file(self, episode: int|None, agent: str) -> str:
    return "%s/%s.pickle" % (self.agents_dir(episode), agent)

  def training_metrics_dir(self) -> str:
    return ensure_dir("%s/training" % (self.artifacts.metrics))

  def training_metrics_file(self, episode: int) -> str:
    return "%s/%s.csv" % (self.training_metrics_dir(), episode)

  def evaluation_metrics_dir(self) -> str:
    return ensure_dir("%s/evaluation" % (self.artifacts.metrics))

  def evaluation_metrics_file(self, episode: int) -> str:
    return "%s/%s.csv" % (self.evaluation_metrics_dir(), episode)

  def training_plots_dir(self, label: str) -> str:
    return ensure_dir("%s/training/%s" % (self.artifacts.plots, label))

  def training_plots_file(self, label: str, episode: int|None) -> str:
    if episode is None:
      return "%s/summary.png" % (self.training_plots_dir(label))
    return "%s/%s.png" % (self.training_plots_dir(label), episode)

  def evaluation_plots_dir(self, label: str) -> str:
    return ensure_dir("%s/evaluation/%s" % (self.artifacts.plots, label))

  def evaluation_plots_file(self, label: str, episode: int|None) -> str:
    if episode is None:
      return "%s/summary.png" % (self.evaluation_plots_dir(label))
    return "%s/%s.png" % (self.evaluation_plots_dir(label), episode)
