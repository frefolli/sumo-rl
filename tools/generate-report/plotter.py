import matplotlib.pyplot
import numpy
import os
from sumo_rl.models.commons import ensure_dir

class Plotter:
  @staticmethod
  def extract_metric(rounds: dict, metric: str):
    result = {}
    for object_key, object_data in rounds.items():
      result[object_key] = object_data[metric]
    return result

  @staticmethod
  def create(output_dir: str, rounds: dict, metrics: list[str], mean: bool = False):
    ensure_dir(output_dir)
    for metric in metrics:
      metric_data = Plotter.extract_metric(rounds, metric)
      matplotlib.pyplot.figure(figsize=(10, 5))
      for object_key, object_value in metric_data.items():
        Ys = object_value
        Xs = list(range(len(Ys)))
        if mean:
          Ys = [numpy.mean(Ys)] * len(Xs)
          matplotlib.pyplot.plot(Xs, Ys, label=object_key)
        else:
          matplotlib.pyplot.plot(Xs, Ys, label=object_key, marker='o')
      matplotlib.pyplot.title(metric)
      matplotlib.pyplot.legend()
      matplotlib.pyplot.tight_layout()
      filepath = os.path.join(output_dir, '%s.png' % metric)
      matplotlib.pyplot.savefig(filepath)
      print('Written', filepath)
      matplotlib.pyplot.close()
