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
  A = load_rounds('./experiments/E8/rounds')
  B = load_rounds('./experiments/E9/rounds')

  # Equal header
  assert A[0] == B[0]
  # Equal number of rounds
  assert len(A[1]) == len(B[1])

  dirpath = './experiments/E7/rounds'
  for i in range(len(A[1])):
    filepath = os.path.join(dirpath, '%s.csv' % i)
    head = A[0]
    body = A[1][i] + B[1][i]
    content = '\n'.join([head] + body)
    with open(filepath, 'w') as file:
      file.write(content)
