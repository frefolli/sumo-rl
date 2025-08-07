import pandas
import os
 
class Rounds:
  @staticmethod
  def load(exp_id: str):
    return Rounds.fetch(exp_id)

  @staticmethod
  def fetch(exp_id: str):
    basepath = './experiments/%s/rounds' % exp_id
    rounds = []
    for file in os.listdir(basepath):
      path = os.path.join(basepath, file)
      id = int(file.split('.')[0])
      round = Rounds.read(pandas.read_csv(path))
      rounds.append((round, id))
    rounds = sorted(rounds, key = lambda k: k[1])
    return Rounds.arrange(rounds)

  @staticmethod
  def find_variants(df: pandas.DataFrame) -> dict[str, str]:
    ids = [str(_).split('-') for _ in df['ID']]
    max_len = max([len(id) for id in ids])
    assert (max_len > 0)
    ids = [ id + ['' for _ in range(max_len - len(id))] for id in ids ]
    varadics = []
    for idx in range(max_len):
      for prec, succ in zip(ids, ids[1:]):
        if prec[idx] != succ[idx]:
          varadics.append(idx)
          break
    variants = {}
    for id in ids:
      raw_id = '-'.join(list(filter(lambda k: len(k) > 0, id)))
      var_id = '-'.join(list(filter(lambda k: len(k) > 0, [ id[idx] for idx in varadics ])))
      variants[raw_id] = var_id
    return variants

  @staticmethod
  def read(df: pandas.DataFrame) -> dict:
    objects = {}
    var_map = Rounds.find_variants(df)
    for _, row in df.iterrows():
      objects[var_map[str(row['ID'])]] = {
        metric: row[metric]
        for metric in [
          'arrival_rate_mean', 'departure_rate_mean',
          'speed_var', 'speed_mean',
          'accumulated_waiting_time_mean', 'accumulated_waiting_time_var',
          'waiting_time_mean', 'waiting_time_var',
          ]
      }
    return objects

  @staticmethod
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
