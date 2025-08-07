from tools.executor.experiment import Experiment
from tools.executor.archive import Archive, Configuration, use_iterations, exec_cmd
from sumo_rl.models.commons import ensure_dir
import random

class SequentialExperiment(Experiment):
  def __init__(self, id: str, name: str, archive: Archive, skip_training: bool = False, skip_evaluation: bool = False) -> None:
    super().__init__(id, name, archive, skip_training, skip_evaluation)
    self.configurations: list[Configuration] = []

  def prepare(self):
    exec_cmd('rm -rf ./archive')
    exec_cmd('rm -rf experiments/%s.tar' % (self.id))
    exec_cmd('rm -rf experiments/%s.tar.zst' % (self.id))
    exec_cmd('rm -rf experiments/%s/rounds.tar' % (self.id))
    exec_cmd('rm -rf experiments/%s/rounds' % (self.id))
    ensure_dir('experiments/%s/rounds' % self.id)

  def training(self):
    seed = random.randint(0, 10000)
    for _ in use_iterations(1):
      for CONFIGURATION in self.configurations:
        self.archive.switch(CONFIGURATION)
        args = ['python', '-m', 'main', '-r', '-DT', '-S', str(seed)]
        args += self.archive.config.to_cli()
        exec_cmd(' '.join(args))
        #exec_cmd('python -m tools.plot2')

  def evaluation(self):
    for i in use_iterations(5):
      seed = random.randint(0, 10000)
      for CONFIGURATION in self.configurations:
        self.archive.switch(CONFIGURATION)
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
