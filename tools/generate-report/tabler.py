import matplotlib.pyplot
import numpy
import os
from sumo_rl.models.commons import ensure_dir

class Tabler:
  @staticmethod
  def extract_metrics(rounds: dict, metrics: dict[str, bool]) -> list[list]:
    data = {object_key: {metric: numpy.mean(values) for metric, values in object_data.items()} for object_key, object_data in rounds.items()}

    result = []
    for object_key, object_data in data.items():
      result.append([object_key] + [object_data[metric] for metric in metrics])
    return result

  @staticmethod
  def create(output_dir: str, rounds: dict, metrics: dict[str, bool]):
    ensure_dir(output_dir)
    data = Tabler.extract_metrics(rounds, metrics)
    fields = ["ID"] + list(metrics.keys())
    header = "| " + " | ".join(fields) + " |"
    line = "| " + " | ".join(["---" for _ in fields]) + " |"
    rows = ["| " + " | ".join([str(value) for value in row]) + " |" for row in data]
    content = "\n".join([header, line] + rows)
    filepath = os.path.join(output_dir, "total.md")
    with open(filepath, "w") as file:
      file.write(content)
    print('Written', filepath)
