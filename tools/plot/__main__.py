from __future__ import annotations

import typing
import pandas
import matplotlib.pyplot
import sumo_rl.util.config
import argparse
import sys
import enum
import os

class Datastore:
  class Mode(enum.Enum):
    TRAINING='training'
    EVALUATION='evaluation'

  def __init__(self, config: sumo_rl.util.config.Config, mode: Datastore.Mode) -> None:
    self.config = config
    self.mode = mode
    self.episodes = self._identify_episodes()
    self.metrics: dict[int, pandas.DataFrame] = self._load_metrics()

  def _identify_episodes(self) -> list[int]:
    if self.mode == Datastore.Mode.EVALUATION:
      basedir = self.config.evaluation_metrics_dir()
      return [int(file.split('.')[0]) for file in os.listdir(basedir)]
    elif self.mode == Datastore.Mode.TRAINING:
      basedir = self.config.training_metrics_dir()
      return [int(file.split('.')[0]) for file in os.listdir(basedir)]
    else:
      raise ValueError(self.mode)

  def _load_metrics(self) -> dict[int, pandas.DataFrame]:
    metrics = {}
    for episode in self.episodes:
      df = pandas.read_csv(self.metrics_file(episode))
      df = df.dropna()
      metrics[episode] = df
    return metrics

  def metrics_file(self, episode) -> str:
    if self.mode == Datastore.Mode.EVALUATION:
      return self.config.evaluation_metrics_file(episode)
    elif self.mode == Datastore.Mode.TRAINING:
      return self.config.training_metrics_file(episode)
    else:
      raise ValueError(self.mode)

  def plots_file(self, label, episode) -> str:
    if self.mode == Datastore.Mode.EVALUATION:
      return self.config.evaluation_plots_file(label, episode)
    elif self.mode == Datastore.Mode.TRAINING:
      return self.config.training_plots_file(label, episode)
    else:
      raise ValueError(self.mode)

  def __repr__(self) -> str:
    return "Datastore(%s)" % (self.mode,)

class Smoother:
  @staticmethod
  def Symmetric(data: list, K: int) -> list:
    """Smooths data[0:N] by factor K returning output[0:N], where K <= N"""
    N = len(data)
    assert K <= N
    half_K = K // 2
    output = []
    for i in range(N):
      lbound = i - half_K
      if lbound < 0:
        lbound = 0
      hbound = i + half_K
      if hbound > N:
        hbound = N
      value = sum(data[lbound:hbound])/len(data[lbound:hbound])
      output.append(value)
    return output
  
  @staticmethod
  def Asymmetric(data: list, K: int) -> list:
    """Smooths data[0:N] by factor K returning output[0:M], with K <= N and M <= N"""
    N = len(data)
    assert K <= N
    output = []
    for i in range(N):
      lbound = i
      hbound = i + K
      if hbound > N:
        break
      value = sum(data[lbound:hbound])/len(data[lbound:hbound])
      output.append(value)
    return output

  @staticmethod
  def Apply(retriever: Retriever, symmetric: bool) -> Retriever:
    if symmetric:
      return lambda df: Smoother.Symmetric(retriever(df), 500)
    return lambda df: Smoother.Asymmetric(retriever(df), 500)

class Plotter:
  @staticmethod
  def Single(datastore: Datastore, label: str, retrieve_data: Retriever):
    for episode in datastore.metrics.keys():
      df = datastore.metrics[episode]
      _ = matplotlib.pyplot.figure(figsize=(20, 10))
      Ys = retrieve_data(df)
      Xs = [_ for _ in range(len(Ys))]
      matplotlib.pyplot.plot(Xs, Ys, marker='o', label=label)
      matplotlib.pyplot.title('Metrics for episode %s' % (episode))
      matplotlib.pyplot.legend()
      matplotlib.pyplot.savefig(datastore.plots_file(label, episode))
      matplotlib.pyplot.close()
  
  @staticmethod
  def Summary(datastore: Datastore, label: str, retrieve_data: typing.Callable):
    _ = matplotlib.pyplot.figure(figsize=(50, 10))
    Ys = []
    for episode in datastore.metrics.keys():
      df = datastore.metrics[episode]
      Ys += retrieve_data(df)
    Xs = [_ for _ in range(len(Ys))]
    matplotlib.pyplot.plot(Xs, Ys, marker='o', label=label)
    matplotlib.pyplot.title('Metrics summary' % ())
    matplotlib.pyplot.legend()
    matplotlib.pyplot.savefig(datastore.plots_file(label, None))
    matplotlib.pyplot.close()

Retriever = typing.Callable[[pandas.DataFrame], list]

class Plot:
  def __init__(self, datastore: Datastore, label: str, retrieve_data: Retriever, single: bool, summary: bool):
    self.datastore = datastore
    self.label = label
    self.retrieve_data = retrieve_data
    self.single = single
    self.summary = summary

  def plot(self):
    if self.single:
      Plotter.Single(self.datastore, self.label, self.retrieve_data)
    if self.summary:
      Plotter.Summary(self.datastore, self.label, self.retrieve_data)
    print(self)

  def copy(self):
    return Plot(self.datastore, self.label, self.retrieve_data, self.single, self.summary)

  def __repr__(self) -> str:
    return "Plot(%s, %s)" % (self.datastore, self.label)

class Preprocessor:
  @staticmethod
  def InitialSubset(datastore: Datastore) -> list[Plot]:
    plots = []
    # plots.append(Plot(datastore, "total_reward", lambda df: list(df['total_reward']), True, True))
    # plots.append(Plot(datastore, "total_waiting_time", lambda df: list(df['total_waiting_time']), True, True))
    # plots.append(Plot(datastore, "mean_waiting_time", lambda df: list(df['mean_waiting_time']), True, True))
    # plots.append(Plot(datastore, "mean_speed", lambda df: list(df['mean_speed']), True, True))
    plots.append(Plot(datastore, "total_reward", lambda df: list(df['total_reward']), False, True))
    # plots.append(Plot(datastore, "total_waiting_time", lambda df: list(df['total_waiting_time']), False, True))
    # plots.append(Plot(datastore, "mean_waiting_time", lambda df: list(df['mean_waiting_time']), False, True))
    # plots.append(Plot(datastore, "mean_speed", lambda df: list(df['mean_speed']), False, True))
    return plots

  @staticmethod
  def InitialSet(config: sumo_rl.util.config.Config) -> list[Plot]:
    training_datastore = Datastore(config, Datastore.Mode.TRAINING)
    evaluation_datastore = Datastore(config, Datastore.Mode.EVALUATION)

    plots = []
    plots += Preprocessor.InitialSubset(training_datastore)
    plots += Preprocessor.InitialSubset(evaluation_datastore)
    return plots

  @staticmethod
  def ApplySmoothing(plots: list[Plot]) -> list[Plot]:
    output = []
    for plot in plots:
      output.append(plot)
      with_asym_smoothing = plot.copy()
      with_asym_smoothing.label = with_asym_smoothing.label + '-AS'
      with_asym_smoothing.retrieve_data = Smoother.Apply(with_asym_smoothing.retrieve_data, False)
      output.append(with_asym_smoothing)
      with_sym_smoothing = plot.copy()
      with_sym_smoothing.label = with_sym_smoothing.label + '-SS'
      with_sym_smoothing.retrieve_data = Smoother.Apply(with_asym_smoothing.retrieve_data, True)
      output.append(with_sym_smoothing)
    return output

if __name__ == "__main__":
  cli = argparse.ArgumentParser(sys.argv[0])
  cli.add_argument('-C', '--config', default='./config.yml', help="Selects YAML config (defaults to ./config.yml)")
  cli_args = cli.parse_args(sys.argv[1:])
  config = sumo_rl.util.config.Config.from_yaml_file(cli_args.config)

  plots = Preprocessor.ApplySmoothing(Preprocessor.InitialSet(config))
  # plots = Preprocessor.InitialSet(config)
  for plot in plots:
    plot.plot()
