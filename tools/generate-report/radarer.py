import matplotlib.pyplot
import numpy
import os
from sumo_rl.models.commons import ensure_dir

class Radarer:
  @staticmethod
  def normalize(value: float, meanv: float, stdv: float, minv: float, maxv: float, do_not_invert: bool) -> float:
    if not do_not_invert:
      value = maxv - value
    return (value - minv) / (maxv - minv + 1e-9)

  @staticmethod
  def normalize2(value: float, meanv: float, stdv: float, minv: float, maxv: float, do_not_invert: bool) -> float:
    value = (value - minv) / (maxv - minv + 1e-9)
    if not do_not_invert:
      value = 1.0 - value
    return value + 1.5

  @staticmethod
  def normalize3(value: float, meanv: float, stdv: float, minv: float, maxv: float, do_not_invert: bool) -> float:
    eps = 1e-9

    # Step 1: log transform to dampen raw magnitude
    log_val = numpy.log1p(value)
    log_min = numpy.log1p(minv)
    log_max = numpy.log1p(maxv)
    log_mean = numpy.log1p(meanv)
    log_std = numpy.log1p(stdv) if stdv > 0 else 1.0

    # --- Base min-max scaling ---
    mm = (log_val - log_min) / (log_max - log_min + eps)

    # --- Z-score scaling + logistic squash ---
    z = (log_val - log_mean) / (log_std + eps)
    z = 1 / (1 + numpy.exp(-z))  # squash to [0,1]

    # --- Excitement factor (relative variation) ---
    cv = stdv / (meanv + eps)
    alpha = cv / (cv + 1.0)   # 0 = boring, 1 = very exciting

    # --- Blend ---
    norm_val = (1 - alpha) * mm + alpha * z

    # Step 2: optional inversion
    if not do_not_invert:
        norm_val = 1.0 - norm_val

    # Step 3: scale into [0, 3]
    return norm_val * 3.0

  @staticmethod
  def normalize4(value: float, meanv: float, stdv: float, minv: float, maxv: float, do_not_invert: bool) -> float:
    value = (value - meanv) / pow(stdv, 2)
    # if not do_not_invert:
    #   value = - value
    return value

  @staticmethod
  def extract_metrics(rounds: dict, metrics: dict[str, bool], normalizer):
    data = {object_key: {metric: numpy.mean(values) for metric, values in object_data.items()} for object_key, object_data in rounds.items()}
    means = {metric: numpy.mean([object_data[metric] for object_data in data.values()]) for metric in metrics}
    stds = {metric: numpy.std([object_data[metric] for object_data in data.values()]) for metric in metrics}
    mins = {metric: numpy.min([object_data[metric] for object_data in data.values()]) for metric in metrics}
    maxs = {metric: numpy.max([object_data[metric] for object_data in data.values()]) for metric in metrics}

    result = []
    for object_key, object_data in data.items():
      obj = {"ID": object_key, "values": []}
      for metric in metrics:
        obj["values"].append(normalizer(object_data[metric], means[metric], stds[metric], mins[metric], maxs[metric], metrics[metric]))
      result.append(obj)
    return result

  @staticmethod
  def create(output_dir: str, rounds: dict, metrics: dict[str, bool]):
    ensure_dir(output_dir)

    N = len(metrics)
    angles = numpy.linspace(0, 2 * numpy.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    for idx, functor in enumerate([Radarer.normalize, Radarer.normalize2, Radarer.normalize3, Radarer.normalize4]):
      data = Radarer.extract_metrics(rounds, metrics, functor)
      print(data)
      fig, ax = matplotlib.pyplot.subplots(figsize=(10,10), subplot_kw=dict(polar=True))
      for record in data:
          values = record["values"]
          values += values[:1]
          ax.plot(angles, values, label=record["ID"])
          ax.fill(angles, values, alpha=0.1)

      ax.set_xticks(angles[:-1])
      ax.set_xticklabels([_.replace('_', '\n') for _ in metrics], fontsize=18)
      ax.set_yticklabels([])

      matplotlib.pyplot.legend(fontsize=18)
      matplotlib.pyplot.tight_layout()
      filepath = os.path.join(output_dir, "total%s.png" % idx)
      matplotlib.pyplot.savefig(filepath)
      print('Written', filepath)
      matplotlib.pyplot.close()
