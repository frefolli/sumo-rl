from __future__ import annotations

import json
import numpy
import pandas
import matplotlib.pyplot
from sumo_rl.models.serde import GenericFile
import sumo_rl.util.color
import sumo_rl.util.config
import sumo_rl.models.flows
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
    self.route_files = self._identify_route_files()
    self.metrics: dict[int, pandas.DataFrame] = self._load_metrics()
    self.routes: dict[int, pandas.DataFrame] = self._load_routes()
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

  def _identify_route_files(self) -> list[str]:
    routes = []
    if self.mode == Datastore.Mode.EVALUATION:
      routes = self.config.scenario.evaluation_routes
    elif self.mode == Datastore.Mode.TRAINING:
      routes = self.config.scenario.training_routes
    else:
      raise ValueError(self.mode)
    return routes

  def _load_routes(self) -> dict[int, dict[str, numpy.array]]:
    result = {}
    for route_idx, route_file_path in enumerate(self.route_files):
      flows = sumo_rl.models.flows.read_flows_with_occupancy_from_routes_file(route_file_path)
      splitted_by_from = {}
      for flow in flows.values():
        splitted_by_from[flow['from']] = (splitted_by_from.get(flow['from']) or []) + [flow]
      vehs_over_time_by_from = {}
      for from_, flows in splitted_by_from.items():
        splitted_by_begin = {}
        for flow in flows:
          splitted_by_begin[flow['begin']] = (splitted_by_begin.get(flow['begin']) or []) + [flow]
          assert splitted_by_begin[flow['begin']][0]['end'] == splitted_by_begin[flow['begin']][-1]['end']
        vehs_over_time = []
        for begin in sorted(splitted_by_begin.keys()):
          flows = splitted_by_begin[begin]
          mean = numpy.mean([flow['vehs'] for flow in flows])
          head = flows[0]
          vehs_over_time += [mean for _ in range(head['begin'], head['end'])]
        vehs_over_time_by_from[from_] = numpy.array(vehs_over_time)
      result[route_idx] = vehs_over_time_by_from
    return result

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

class Smoother:
  @staticmethod
  def Symmetric(data: numpy.ndarray, K: int) -> numpy.ndarray:
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
    return numpy.array(output)
  
  @staticmethod
  def Asymmetric(data: numpy.ndarray, K: int) -> numpy.ndarray:
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
    return numpy.array(output)

class Slotter:
  @staticmethod
  def Apply(data: numpy.ndarray, K: int) -> numpy.ndarray:
    """Slots data[0:N] by factor K returning output[0:N//K], where K <= N"""
    N = len(data)
    assert K <= N
    output = []
    i = 0
    while i <= N:
      value = data[i:i+K].mean()
      output.append(value)
      i += K
    return numpy.array(output)

class Accumulator:
  @staticmethod
  def Apply(array: numpy.ndarray) -> numpy.ndarray:
    val = 0
    output = []
    for value in array:
      val += value
      output.append(val)
    return numpy.array(output)

class Normalizer:
  @staticmethod
  def Apply(array: numpy.ndarray) -> numpy.ndarray:
    max_v = numpy.max(array)
    min_v = numpy.min(array)
    delta = max_v - min_v
    result = (array - min_v) / delta
    assert 1.0 in result
    return result

class DirectionalSmoother:
  @staticmethod
  def Apply(dirs: dict[str, numpy.ndarray], K: int) -> dict:
    return {key:Smoother.Symmetric(value, K=K) for key,value in dirs.items()}

class DirectionalSlotter:
  @staticmethod
  def Apply(dirs: dict[str, numpy.ndarray], K: int) -> dict:
    return {key:Slotter.Apply(value, K=K) for key,value in dirs.items()}

class DirectionalAccumulator:
  @staticmethod
  def Apply(dirs: dict[str, numpy.ndarray]) -> dict:
    return {key:Accumulator.Apply(value) for key,value in dirs.items()}

class DirectionalNormalizer:
  @staticmethod
  def Apply(dirs: dict[str, numpy.ndarray]) -> dict:
    return {key:Normalizer.Apply(value) for key,value in dirs.items()}

class Plotter:
  COLOR_CACHE={}
  @staticmethod
  def RandomColors(track: list) -> list:
    if len(track) in Plotter.COLOR_CACHE:
      return Plotter.COLOR_CACHE[len(track)]
    colors = sumo_rl.util.color.service(len(track))
    colors = ['#' + color + '33' for color in colors]
    Plotter.COLOR_CACHE[len(track)] = colors
    return Plotter.COLOR_CACHE[len(track)]
  
  @staticmethod
  def ProcessTrack(track: list, Xs_length: int) -> list:
    track_width = Xs_length / len(track)
    tracks = []
    colors = Plotter.RandomColors(track)
    for i in range(len(track)):
      xmin, xmax = i * track_width, (i + 1) * track_width
      label = track[i]
      tracks.append((xmin, xmax, colors[i], label))
    return tracks

  @staticmethod
  def Directional(dirs: dict[str, numpy.ndarray], filepath: str, title: str, track: list = []):
    _ = matplotlib.pyplot.figure(figsize=(50, 10))
    for dir_key, dir_data in dirs.items():
      Ys = dir_data
      Xs = [_ for _ in range(len(Ys))]
      matplotlib.pyplot.plot(Xs, Ys, marker='o', label=dir_key)
      if len(track) > 0:
        for (xmin, xmax, color, label) in Plotter.ProcessTrack(track, len(Xs)):
          matplotlib.pyplot.axvspan(xmin, xmax, color=color) # , label=label
    matplotlib.pyplot.title(title)
    matplotlib.pyplot.legend()
    matplotlib.pyplot.savefig(filepath)
    print(filepath)
    matplotlib.pyplot.close()

def flatize_record_via_symmetry(record: dict) -> dict:
  dirs = {}
  for key, value in record.items():
    if key[::-1] in dirs:
      dirs[key[::-1]] = numpy.mean([dirs[key[::-1]], value])
    else:
      dirs[key] = value
  return dirs

def flatize_record_via_head(record: dict) -> dict:
  dirs = {}
  for key, value in record.items():
    course = key.split('-')
    if course[0] in dirs:
      dirs[course[0]].append(value)
    else:
      dirs[course[0]] = [value]
  return {key:numpy.mean(value) for key,value in dirs.items()}

def divide_by_dirs(Ys: numpy.ndarray) -> dict:
  dirs: dict[str, list] = {}
  for idx, record in enumerate(Ys):
    record = flatize_record_via_head(record)
    for key, value in record.items():
      if key not in dirs:
        dirs[key] = [0.0 for _ in range(idx)]
      dirs[key].append(value)
  return {key:numpy.array(value) for key,value in dirs.items()}

def interpret_dicts(Ys: numpy.ndarray) -> numpy.ndarray:
  return numpy.array([json.loads(_.replace('\'', '"')) for _ in Ys])

if __name__ == "__main__":
  cli = argparse.ArgumentParser(sys.argv[0])
  cli.add_argument('-C', '--config', default='./config.yml', help="Selects YAML config (defaults to ./config.yml)")
  cli_args = cli.parse_args(sys.argv[1:])
  config = sumo_rl.util.config.Config.from_yaml_file(cli_args.config)

  for mode in [Datastore.Mode.EVALUATION]:
    datastore = Datastore(config, mode)
    for episode in datastore.episodes:
      label = 'vehs'
      Ys = datastore.routes[episode]
      smoothed_Ys = DirectionalSlotter.Apply(Ys, 100)
      Plotter.Directional(Ys, datastore.plots_file(label, episode), label)
      Plotter.Directional(smoothed_Ys, datastore.plots_file('smoothed_%s' % label, episode), 'smoothed_%s' % label)

  for mode in [Datastore.Mode.EVALUATION]:
    datastore = Datastore(config, mode)
    #for label in ['awtxdir']:
    for label in ['mean_awt_xdir', 'median_awt_xdir', 'std_awt_xdir']:
      for episode in datastore.episodes:
        Ys = divide_by_dirs(interpret_dicts(datastore.extract(episode, label)))
        track = datastore.track(episode)
        smoothed_Ys = DirectionalSlotter.Apply(Ys, 100)
        Plotter.Directional(Ys, datastore.plots_file(label, episode), label)#, track=track
        Plotter.Directional(smoothed_Ys, datastore.plots_file('smoothed_%s' % label, episode), 'smoothed_%s' % label)#, track=track
