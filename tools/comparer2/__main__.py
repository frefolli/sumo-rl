import os
import pandas
from sumo_rl.models.serde import GenericFile

def destructure(record: dict) -> dict:
  result = {}
  for key in record.keys():
    for key2 in record[key].keys():
      result['%s_%s' % (key, key2)] = record[key][key2]
  return result

def linearize_comparison(scores: list):
  """
    (id, {
      metric: {
        dir: {
          mean: V,
          min: V,
          max: V,
          median: V,
          var: V
        }
      }
    })
  """
  pass

  metrics = set(list(scores[0][1].keys()))
  for score in scores:
    metrics &= score[1].keys()

  comparisons = {}
  for value in ['mean', 'median', 'var', 'min', 'max']:
    for metric in metrics:
      records = []
      for (variant_id, variant_data) in scores:
        record = {'ID': variant_id}
        variant_metric_data = variant_data[metric]
        for dir_id, dir_data in variant_metric_data.items():
          record[dir_id] = float(dir_data[value])
        records.append(record)
      comparisons[(metric, value)] = records
  return comparisons

def load_all_scores():
  for file in os.listdir('./archive'):
    if os.path.isdir('./archive/%s' % file):
      path = './archive/%s/metrics/evaluation/scores.yml' % file
      if os.path.exists(path):
        yield (file, GenericFile.from_yaml_file(path).to_dict())

if __name__ == '__main__':
  records = list(load_all_scores())
  comparisons = linearize_comparison(records)
  GenericFile(comparisons).to_yaml_file('scores.yml')
