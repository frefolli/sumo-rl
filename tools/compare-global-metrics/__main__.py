import os
import pandas
from sumo_rl.models.serde import GenericFile

def destructure(record: dict) -> dict:
  result = {}
  for key in record.keys():
    for key2 in record[key].keys():
      result['%s_%s' % (key, key2)] = record[key][key2]
  return result

def load_all_scores():
  for file in os.listdir('./archive'):
    if os.path.isdir('./archive/%s' % file):
      path = './archive/%s/metrics/evaluation/scores.yml' % file
      if os.path.exists(path):
        yield (file, GenericFile.from_yaml_file(path).to_dict())

if __name__ == '__main__':
  records = list(map(lambda record: {'ID': record[0], **destructure(record[1])}, load_all_scores()))
  df = pandas.DataFrame(records)
  df.to_csv('scores.csv', index=False)
