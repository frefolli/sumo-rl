import numpy
import matplotlib.pyplot
import os
from sumo_rl.models.commons import ensure_dir

class Leaderboard:
  @staticmethod
  def fibonacci(nums: int) -> list[int]:
    if nums < 0:
      raise ValueError(nums)
    elif nums == 0:
      return []
    elif nums == 1:
      return [1]
    else:
      arr = [1, 2]
      for i in range(2, nums):
        arr.append(arr[-1] + arr[-2])
      return arr

  @staticmethod
  def fibonaccik(nums: int, skip_k: int) -> list[int]:
    return Leaderboard.fibonacci(nums + skip_k)[skip_k:]

  @staticmethod
  def assign_points(objects: dict[str, dict], metric: str, higher_is_better: bool = True) -> dict:
    sorted_object_keys: list[str] = []
    if higher_is_better:
      sorted_object_keys = sorted(list(objects.keys()), key = lambda obj: numpy.mean(objects[obj][metric]))
    else:
      sorted_object_keys = sorted(list(objects.keys()), key = lambda obj: -numpy.mean(objects[obj][metric]))
    results = {}
    for idx, obj_points in enumerate(Leaderboard.fibonacci(len(sorted_object_keys))):
      results[sorted_object_keys[idx]] = obj_points
    return results

  @staticmethod
  def update_points(consolidated_points: dict, round_points: dict) -> dict:
    results = {}
    for obj_key, obj_points in round_points.items():
      results[obj_key] = (consolidated_points.get(obj_key) or 0) + obj_points
    return results

  @staticmethod
  def build_leaderboards(objects: dict, metrics: dict[str, bool]) -> tuple[list[tuple[str, dict]], dict]:
    leaderboards = []
    results = {}
    for (metric, higher_is_better) in metrics.items():
      round_points = Leaderboard.assign_points(objects, metric, higher_is_better)
      leaderboards.append((metric, round_points))
      results = Leaderboard.update_points(results, round_points)
    return leaderboards, results

  @staticmethod
  def plot_leaderboard(output_dir: str, title: str, data: dict[str, float]):
    fig = matplotlib.pyplot.figure(figsize=(10, 5))
    for object_key, object_value in data.items():
      bar_container = matplotlib.pyplot.bar(object_key, object_value, label=object_key)
      matplotlib.pyplot.bar_label(bar_container, fmt='{:,.0f}')
    matplotlib.pyplot.title(title)
    matplotlib.pyplot.legend()
    matplotlib.pyplot.tight_layout()
    filepath = os.path.join(output_dir, '%s.png' % title)
    matplotlib.pyplot.savefig(filepath)
    print('Written', filepath)
    matplotlib.pyplot.close()

  @staticmethod
  def create(output_dir: str, objects: dict, metrics: dict[str, bool]) -> dict:
    ensure_dir(output_dir)
    leaderboards, results = Leaderboard.build_leaderboards(objects, metrics)
    for (metric, leaderboard) in leaderboards:
      Leaderboard.plot_leaderboard(output_dir, metric, leaderboard)
    Leaderboard.plot_leaderboard(output_dir, 'total', results)
