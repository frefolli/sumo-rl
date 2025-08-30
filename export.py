import os

def exec_cmd(cmd: str) -> None:
  print(">", cmd)
  assert os.system(cmd) == 0

for expID in os.listdir('./experiments'):
  if expID.startswith('EXP'):
    exec_cmd('python -m tools.generate-report -e %s' % (expID))
    exec_cmd('cp experiments/%s/radars/total.png /tmp/%s.png' % (expID, expID.lower()))
    exec_cmd('cp /tmp/%s.png ~/Documents/Github/master-thesis/figures/exp/%s.png' % (expID.lower(), expID.lower()))
