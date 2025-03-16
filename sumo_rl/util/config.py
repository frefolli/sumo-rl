from __future__ import annotations
from sumo_rl.models.serde import SerdeJsonFile, SerdeYamlFile, SerdeDict
from sumo_rl.models.commons import ensure_dir
import os

class SumoConfig(SerdeDict):
  def __init__(self, data: dict):
    self.seconds: int = data['seconds']
    self.min_green: int = data['min_green']
    self.delta_time: int = data['delta_time']
    self.use_gui: bool = data['use_gui']
    self.sumo_seed: int = data['sumo_seed']
    self.further_cmd_args: list[str] = data['further_cmd_args']

  def to_dict(self) -> dict:
    return {
      'seconds': self.seconds,
      'min_green': self.min_green,
      'delta_time': self.delta_time,
      'use_gui': self.use_gui,
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
    self.runs: int = data['runs']
    self.episodes: int = data['episodes']

  def to_dict(self) -> dict:
    return {
      'runs': self.runs,
      'episodes': self.episodes,
    }

  @staticmethod
  def from_dict(data: dict) -> TrainingConfig:
    return TrainingConfig(data)

class EvaluationConfig(SerdeDict):
  def __init__(self, data: dict):
    self.runs: int = data['runs']
    self.episodes: int = data['episodes']

  def to_dict(self) -> dict:
    return {
      'runs': self.runs,
      'episodes': self.episodes,
    }

  @staticmethod
  def from_dict(data: dict) -> EvaluationConfig:
    return EvaluationConfig(data)

class ScenarioConfig(SerdeYamlFile, SerdeJsonFile):
  def __init__(self, data: dict):
    self._path: str = ""
    self._network: str = data['network']
    self._training_routes: list[str] = data['routes']['training']
    self._evaluation_routes: list[str] = data['routes']['evaluation']
    self.network = ""
    self.training_routes = []
    self.evaluation_routes = []

  def set_path(self, path: str):
    self.network = ""
    self.training_routes = []
    self.evaluation_routes = []

    network = os.path.join(path, self._network)
    if not os.path.exists(network):
      raise ValueError("scenario %s declared %s network file but %s doesn't exist" % (path, self._network, network))

    training_routes = []
    for file in self._training_routes:
      qualified = os.path.join(path, file)
      if not os.path.exists(network):
        raise ValueError("scenario %s declared %s training route file but %s doesn't exist" % (path, file, qualified))
      training_routes.append(qualified)

    evaluation_routes = []
    for file in self._evaluation_routes:
      qualified = os.path.join(path, file)
      if not os.path.exists(network):
        raise ValueError("scenario %s declared %s evaluation route file but %s doesn't exist" % (path, file, qualified))
      evaluation_routes.append(qualified)
    
    self._path = path
    self.network = network
    self.training_routes = training_routes
    self.evaluation_routes = evaluation_routes

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
      'scenario': self.scenario.get_path(),
      'artifacts': self.artifacts.to_dict(),
    }

  @staticmethod
  def from_dict(data: dict) -> Config:
    return Config(data)

  def __repr__(self) -> str:
    return self.to_yaml()

  def agents_dir(self, run: int|None, episode: int|None) -> str:
    if episode is None:
      if run is None:
        return ensure_dir("%s/final" % (self.artifacts.agents))
      return ensure_dir("%s/%s/final" % (self.artifacts.agents, run))
    assert run is not None
    return ensure_dir("%s/%s/%s" % (self.artifacts.agents, run, episode))

  def agents_file(self, run: int|None, episode: int|None, agent: int) -> str:
    return "%s/%s.pickle" % (self.agents_dir(run, episode), agent)

  def training_metrics_dir(self, run: int) -> str:
    return ensure_dir("%s/training/%s" % (self.artifacts.metrics, run))

  def training_metrics_file(self, run: int, episode: int) -> str:
    return "%s/%s.csv" % (self.training_metrics_dir(run), episode)

  def evaluation_metrics_dir(self, run: int) -> str:
    return ensure_dir("%s/evaluation/%s" % (self.artifacts.metrics, run))

  def evaluation_metrics_file(self, run: int, episode: int) -> str:
    return "%s/%s.csv" % (self.evaluation_metrics_dir(run), episode)

  def training_plots_dir(self, label: str, run: int) -> str:
    return ensure_dir("%s/training/%s/%s" % (self.artifacts.plots, label, run))

  def training_plots_file(self, label: str, run: int, episode: int|None) -> str:
    if episode is None:
      return "%s/summary.png" % (self.training_plots_dir(label, run))
    return "%s/%s.png" % (self.training_plots_dir(label, run), episode)

  def evaluation_plots_dir(self, label: str, run: int) -> str:
    return ensure_dir("%s/evaluation/%s/%s" % (self.artifacts.plots, label, run))

  def evaluation_plots_file(self, label: str, run: int, episode: int|None) -> str:
    if episode is None:
      return "%s/summary.png" % (self.evaluation_plots_dir(label, run))
    return "%s/%s.png" % (self.evaluation_plots_dir(label, run), episode)
