import os

def exec_cmd(cmd: str) -> None:
  print(">", cmd)
  assert os.system(cmd) == 0

K = 4

document = ""

document += "<html>\n"
document += """
<style>
.experiment-data {
  display: grid;
  grid-template-columns: repeat(%s, %s%%);
}
</style>
""" % (K, round(100 / K, 2))
document += "<body>\n"

for expID in os.listdir('./experiments'):
  if expID.startswith('EXP'):
    exec_cmd('python -m tools.generate-report -e %s' % (expID))
    # exec_cmd('cp experiments/%s/radars/total1.png /tmp/%s.png' % (expID, expID.lower()))
    # exec_cmd('cp /tmp/%s.png ~/Documents/Github/master-thesis/figures/exp/%s.png' % (expID.lower(), expID.lower()))
    document += "<div class=\"experiment\">\n"
    document += "<h1>" + expID + "</h1>\n"
    document += "<div class=\"experiment-data\">\n"
    for idx in range(K):
      document += "<div class=\"plot\">\n"
      document += "<h2>RADAR %s</h2>\n" % idx
      document += "<img width=\"100%\" src=\"" + os.path.join(expID, 'radars', 'total%s.png' % idx) + "\"/>\n"
      document += "</div>\n"
    document += "</div>\n"
    document += "</div>\n"

document += "</body>\n"
document += "</html>\n"

with open("./experiments/README.html", "w") as file:
  file.write(document)
