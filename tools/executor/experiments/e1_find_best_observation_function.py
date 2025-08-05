from tools.executor.experiment import Experiment
from tools.executor.archive import Archive, Configuration, use_iterations, exec_cmd
from sumo_rl.models.commons import ensure_dir
import random

class E1FindBestObservationFunction(Experiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("E1", "FindBestObservationFunction", archive)

  def prepare(self):
    exec_cmd('rm -rf ./archive')
    exec_cmd('rm -rf experiments/%s.tar' % (self.id))
    exec_cmd('rm -rf experiments/%s/rounds.tar' % (self.id))
    exec_cmd('rm -rf experiments/%s/rounds' % (self.id))
    ensure_dir('experiments/%s/rounds' % self.id)

  def training(self):
    OBSERVATIONS = ['default', 's', 'd', 'q']
    seed = random.randint(0, 10000)
    self.archive.switch(Configuration(agent='ql', reward='dwt', observation='default', partition='mono', self_adaptive=False, dataset='frankestein'))
    for _ in use_iterations(1):
      for observation in OBSERVATIONS:
        self.archive.switch(Configuration.Patch(self.archive.config, observation=observation))
        args = ['python', '-m', 'main', '-r', '-DT', '-S', str(seed)]
        args += self.archive.config.to_cli()
        exec_cmd(' '.join(args))
        #exec_cmd('python -m tools.plot2')

  def evaluation(self):
    OBSERVATIONS = ['default', 's', 'd', 'q']
    self.archive.switch(Configuration(agent='ql', reward='dwt', observation='default', partition='mono', self_adaptive=False, dataset='frankestein'))
    for i in use_iterations(5):
      seed = random.randint(0, 10000)
      for observation in OBSERVATIONS:
        self.archive.switch(Configuration.Patch(self.archive.config, observation=observation))
        args = ['python', '-m', 'main', '-r', '-DE', '-S', str(seed)]
        args += self.archive.config.to_cli()
        exec_cmd(' '.join(args))
        exec_cmd('python -m tools.extract-global-metrics')
      exec_cmd('python -m tools.compare-global-metrics')
      exec_cmd('mv scores.csv experiments/%s/rounds/%s.csv' % (self.id, i))

  def pack(self):
    exec_cmd('tar cvf experiments/%s/rounds.tar experiments/%s/rounds' % (self.id, self.id))
    exec_cmd('tar cvf experiments/%s.tar experiments/%s' % (self.id, self.id))
    exec_cmd('zstd experiments/%s.tar' % (self.id))

  def clean(self):
    exec_cmd('rm -rf ./archive')
    exec_cmd('rm -rf experiments/%s.tar' % (self.id))
    exec_cmd('rm -rf experiments/%s/rounds.tar' % (self.id))

  def commit(self):
    exec_cmd('git add experiments/%s.tar.zst' % (self.id))
    exec_cmd('git commit -m "Autocommit for JOB of Experiment %s!"' % (self.id))
    exec_cmd('git push')
