from __future__ import annotations

import numpy
import pandas
from sumo_rl.models.serde import GenericFile
import sumo_rl.util.config
import argparse
import sys
import enum
import os
import json

class Datastore:
  class Mode(enum.Enum):
    TRAINING='training'
    EVALUATION='evaluation'

  def __init__(self, config: sumo_rl.util.config.Config, mode: Datastore.Mode) -> None:
    self.config = config
    self.mode = mode
    self.episodes = self._identify_episodes()
    self.metrics: dict[int, pandas.DataFrame] = self._load_metrics()
    self.tracks = self._identify_tracks()

  def _identify_all_csvs(self, dir: str) -> list[str]:
    files = []
    for file in os.listdir(dir):
      if file.endswith('.csv'):
        files.append(file)
    return files

  def _identify_episodes(self) -> list[int]:
    return [int(file.split('.')[0]) for file in self._identify_all_csvs(self.metrics_dir())]

  def _load_metrics(self) -> dict[int, pandas.DataFrame]:
    metrics = {}
    for episode in self.episodes:
      df = pandas.read_csv(self.metrics_file(episode))
      df = df.dropna()
      metrics[episode] = df
    return metrics

  def _identify_tracks(self) -> dict[int, list[str]]:
    track_file = self.metrics_dir() + '/tracks.yml'
    written_tracks = {}
    if os.path.exists(track_file):
      written_tracks = GenericFile.from_yaml_file(track_file).to_dict()
    actual_tracks = {}
    for episode in self.episodes:
      file = self.metrics_file(episode)
      if file in written_tracks:
        actual_tracks[episode] = written_tracks[file].split('-')
      else:
        actual_tracks[episode] = []
    return actual_tracks

  def metrics_dir(self) -> str:
    if self.mode == Datastore.Mode.EVALUATION:
      return self.config.evaluation_metrics_dir()
    elif self.mode == Datastore.Mode.TRAINING:
      return self.config.training_metrics_dir()
    else:
      raise ValueError(self.mode)

  def metrics_file(self, episode) -> str:
    if self.mode == Datastore.Mode.EVALUATION:
      return self.config.evaluation_metrics_file(episode)
    elif self.mode == Datastore.Mode.TRAINING:
      return self.config.training_metrics_file(episode)
    else:
      raise ValueError(self.mode)

  def plots_file(self, label, episode = None) -> str:
    if self.mode == Datastore.Mode.EVALUATION:
      return self.config.evaluation_plots_file(label, episode)
    elif self.mode == Datastore.Mode.TRAINING:
      return self.config.training_plots_file(label, episode)
    else:
      raise ValueError(self.mode)

  def __repr__(self) -> str:
    return "Datastore(%s)" % (self.mode,)

  def track(self, episode: int) -> list[str]:
    return self.tracks[episode]

  def extract(self, episode: int, label: str) -> numpy.ndarray:
    return numpy.array(self.metrics[episode][label])

  def extract_roll(self, label: str) -> numpy.ndarray:
    result = []
    for episode in self.episodes:
      result += list(self.metrics[episode][label])
    return numpy.array(result)

def divide_by_dirs(Ys: numpy.ndarray) -> dict:
  dirs: dict[str, list] = {}
  for idx, record in enumerate(Ys):
    for key_, value in record.items():
      key = key_.split('-')[0]
      if key not in dirs:
        dirs[key] = [0.0 for _ in range(idx)]
      dirs[key].append(value)
  return {key:numpy.array(value) for key,value in dirs.items()}

def statistical_analysis(Ys: numpy.ndarray) -> dict:
  dirs: dict[str, numpy.ndarray] = divide_by_dirs(Ys)
  return {dir_key: {
    'mean': dir_data.mean(),
    'median': numpy.median(dir_data),
    'var': dir_data.var(),
    'min': dir_data.min(),
    'max': dir_data.max(),
  } for dir_key, dir_data in dirs.items()}

def interpret_dicts(Ys: numpy.ndarray) -> numpy.ndarray:
  return numpy.array([json.loads(_.replace('\'', '"')) for _ in Ys])

def compute_stricly_positive_differential(Ys: numpy.ndarray) -> numpy.ndarray:
  return numpy.array([
    Ys[i + 1] - Ys[i]
    for i in range(0, len(Ys) - 1)
    if Ys[i + 1] >= Ys[i]
  ])

if __name__ == "__main__":
  cli = argparse.ArgumentParser(sys.argv[0])
  cli.add_argument('-C', '--config', default='./config.yml', help="Selects YAML config (defaults to ./config.yml)")
  cli_args = cli.parse_args(sys.argv[1:])
  config = sumo_rl.util.config.Config.from_yaml_file(cli_args.config)

  datastore = Datastore(config, Datastore.Mode.EVALUATION)
  data = {}
  data['mean_awt_xdir'] = interpret_dicts(datastore.extract_roll('mean_awt_xdir'))
  data['median_awt_xdir'] = interpret_dicts(datastore.extract_roll('median_awt_xdir'))
  data['std_awt_xdir'] = interpret_dicts(datastore.extract_roll('std_awt_xdir'))
  scores = {}
  labels = [
    'mean_awt_xdir',
    'median_awt_xdir',
    'std_awt_xdir'
  ]
  for label in labels:
    scores[label] = statistical_analysis(data[label])
  print(scores)
  GenericFile(scores).to_yaml_file(os.path.join(datastore.metrics_dir(), 'scores.yml'))
