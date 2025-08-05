import matplotlib.pyplot
import numpy
import os
from sumo_rl.models.commons import ensure_dir

class Barrer:
  @staticmethod
  def extract_metric(rounds: dict, metric: str):
    result = {}
    for object_key, object_data in rounds.items():
      result[object_key] = object_data[metric]
    return result

  @staticmethod
  def create(output_dir: str, rounds: dict, metrics: list[str]):
    ensure_dir(output_dir)
    for metric in metrics:
      metric_data = Barrer.extract_metric(rounds, metric)
      matplotlib.pyplot.figure(figsize=(10, 5))
      for object_key, object_value in metric_data.items():
        matplotlib.pyplot.bar(object_key, numpy.mean(object_value), label=object_key)
      matplotlib.pyplot.title(metric)
      matplotlib.pyplot.legend()
      matplotlib.pyplot.tight_layout()
      filepath = os.path.join(output_dir, '%s.png' % metric)
      matplotlib.pyplot.savefig(filepath)
      print('Written', filepath)
      matplotlib.pyplot.close()
