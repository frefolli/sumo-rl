import pandas
import os
import matplotlib.pyplot
import numpy

def load_rounds(exp_id: str):
  def read(df: pandas.DataFrame) -> dict:
    objects = {}
    for idx, row in df.iterrows():
      objects[row['ID'].split('-')[3]] = {
        metric: row[metric]
        for metric in ['arrival_rate_mean', 'departure_rate_mean', 'speed_mean', 'accumulated_waiting_time_mean', 'waiting_time_mean']
      }
    return objects

  def arrange(rounds: list[dict]):
    objects: dict = {}
    for round in rounds:
      for object_key, object_data in round[0].items():
        if object_key not in objects:
          objects[object_key] = {}
        objects[object_key] = {
          metric: (objects[object_key].get(metric) or []) + [value]
          for metric, value in object_data.items()
        }
    return objects
  
  def fetch():
    basepath = './experiments/%s/rounds' % exp_id
    rounds = []
    for file in os.listdir(basepath):
      path = os.path.join(basepath, file)
      id = int(file.split('.')[0])
      round = read(pandas.read_csv(path))
      rounds.append((round, id))
    rounds = sorted(rounds, key = lambda k: k[1])
    return arrange(rounds)

  return fetch()

def extract_metric(rounds: dict, metric: str):
  result = {}
  for object_key, object_data in rounds.items():
    result[object_key] = object_data[metric]
  return result

def plot_metrics(rounds: dict, metrics: list[str], mean: bool = False):
  for metric in metrics:
    metric_data = extract_metric(rounds, metric)
    fig = matplotlib.pyplot.figure(figsize=(10, 5))
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
    matplotlib.pyplot.savefig('/tmp/plot-%s.png' % metric)
    matplotlib.pyplot.close()

def bar_metrics(rounds: dict, metrics: list[str]):
  for metric in metrics:
    metric_data = extract_metric(rounds, metric)
    fig = matplotlib.pyplot.figure(figsize=(10, 5))
    for object_key, object_value in metric_data.items():
      matplotlib.pyplot.bar(object_key, numpy.mean(object_value), label=object_key)
    matplotlib.pyplot.title(metric)
    matplotlib.pyplot.legend()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('/tmp/bar-%s.png' % metric)
    matplotlib.pyplot.close()

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

def assign_points(objects: dict[str, dict], metric: str, higher_is_better: bool = True) -> dict:
  sorted_object_keys: list[str] = []
  if higher_is_better:
    sorted_object_keys = sorted(list(objects.keys()), key = lambda obj: numpy.mean(objects[obj][metric]))
  else:
    sorted_object_keys = sorted(list(objects.keys()), key = lambda obj: -numpy.mean(objects[obj][metric]))
  results = {}
  for idx, obj_points in enumerate(fibonacci(len(sorted_object_keys))):
    results[sorted_object_keys[idx]] = obj_points
  return results

def update_points(consolidated_points: dict, round_points: dict) -> dict:
  results = {}
  for obj_key, obj_points in round_points.items():
    results[obj_key] = (consolidated_points.get(obj_key) or 0) + obj_points
  return results

def leaderboard(objects: dict, metrics: dict[str, bool]) -> dict:
  results = {}
  for (metric, higher_is_better) in metrics.items():
    round_points = assign_points(objects, metric, higher_is_better)
    print(round_points)
    results = update_points(results, round_points)
  return results

if __name__ == '__main__':
  metrics = {
    'arrival_rate_mean': True,
    'departure_rate_mean': True,
    'speed_mean': True,
    'accumulated_waiting_time_mean': False,
    'waiting_time_mean': False,
  }

  rounds = load_rounds('E0')
  plot_metrics(rounds, metrics, mean=False)
  bar_metrics(rounds, metrics)
  leaderboard(rounds, metrics)
