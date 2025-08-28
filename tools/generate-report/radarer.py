import matplotlib.pyplot
import numpy
import os
from sumo_rl.models.commons import ensure_dir

class Radarer:
  @staticmethod
  def normalize(value: float, minv: float, maxv: float, do_not_invert: bool) -> float:
    if not do_not_invert:
      value = maxv - value
    return (value - minv) / (maxv - minv + 1e-9)

  @staticmethod
  def extract_metrics(rounds: dict, metrics: dict[str, bool]):
    data = {object_key: {metric: numpy.mean(values) for metric, values in object_data.items()} for object_key, object_data in rounds.items()}
    mins = {metric: numpy.min([object_data[metric] for object_data in data.values()]) for metric in metrics}
    maxs = {metric: numpy.max([object_data[metric] for object_data in data.values()]) for metric in metrics}

    result = []
    for object_key, object_data in data.items():
      obj = {"ID": object_key, "values": []}
      for metric in metrics:
        obj["values"].append(Radarer.normalize(object_data[metric], mins[metric], maxs[metric], metrics[metric]))
      result.append(obj)
    return result

  @staticmethod
  def create(output_dir: str, rounds: dict, metrics: dict[str, bool]):
    ensure_dir(output_dir)

    N = len(metrics)
    angles = numpy.linspace(0, 2 * numpy.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = matplotlib.pyplot.subplots(figsize=(10,10), subplot_kw=dict(polar=True))

    data = Radarer.extract_metrics(rounds, metrics)
    for record in data:
        values = record["values"]
        values += values[:1]
        ax.plot(angles, values, label=record["ID"])
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([_.replace('_', '\n') for _ in metrics], fontsize=12)
    ax.set_yticklabels([])

    matplotlib.pyplot.legend()
    filepath = os.path.join(output_dir, "total.png")
    matplotlib.pyplot.savefig(filepath)
    print('Written', filepath)
    matplotlib.pyplot.close()
