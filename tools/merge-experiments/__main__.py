import os

def load_round(filepath: str) -> tuple[str, list[str]]:
  with open(filepath, 'r') as file:
    lines = file.read().split('\n')
    return lines[0], list(filter(lambda k: len(k) > 0, lines[1:]))

def load_rounds(dirpath: str) -> tuple[str, list[list[str]]]:
  rounds = []
  head = ''
  for file in os.listdir(dirpath):
    if file.endswith('.csv'):
      path = os.path.join(dirpath, file)
      head, body = load_round(path)
      rounds.append(body)
  return head, rounds

if __name__ == '__main__':
  E3A = load_rounds('./E3A/rounds')
  E3B = load_rounds('./E3B/rounds')
  E3C = load_rounds('./E3C/rounds')

  # Equal header
  assert E3A[0] == E3B[0]
  assert E3C[0] == E3B[0]
  # Equal number of rounds
  assert len(E3A[1]) == len(E3B[1])
  assert len(E3C[1]) == len(E3B[1])

  dirpath = './E3/rounds'
  for i in range(len(E3A[1])):
    filepath = os.path.join(dirpath, '%s.csv' % i)
    head = E3A[0]
    body = E3A[1][i] + E3B[1][i] + E3C[1][i]
    content = '\n'.join([head] + body)
    with open(filepath, 'w') as file:
      file.write(content)
