from tools.executor.experiment import Experiment
from tools.executor.archive import Archive, Configuration, use_iterations, exec_cmd
from sumo_rl.models.commons import ensure_dir
import random

class CombinatorialExperiment(Experiment):
  def __init__(self,
               id: str,
               name: str,
               archive: Archive,
               skip_training: bool = False,
               skip_evaluation: bool = False) -> None:
    super().__init__(id, name, archive, skip_training, skip_evaluation)
    self.agents = ['ql']
    self.observations = ['default']
    self.rewards = ['dwt']
    self.partitions = ['mono']
    self.self_adaptives = [False]
    self.datasets = ['frankestein']
    self.shutdowns = [False]
    self.quantizations = [16]
    self.tm_alpha = [0.1]
    self.tm_gamma = [0.9]
    self.eg_epsilon = [1.0]
    self.eg_decay = [0.99]
    self.eg_minimum = [0.05]
    self.nn_deterministic = [False]
    self.nn_buffer_size = [2048]

  def prepare(self):
    if not self.skip_training:
      exec_cmd('rm -rf ./archive')
    exec_cmd('rm -rf ./experiments/%s.tar.zst' % (self.id))
    exec_cmd('rm -rf ./experiments/%s.tar' % (self.id))
    exec_cmd('rm -rf ./experiments/%s/rounds.tar' % (self.id))
    exec_cmd('rm -rf ./experiments/%s/rounds' % (self.id))
    ensure_dir('./experiments/%s/rounds' % self.id)

  def training(self):
    seed = random.randint(0, 10000)
    for _ in use_iterations(1):
      for AGENT in self.agents:
        for OBSERVATION in self.observations:
          for REWARD in self.rewards:
            for PARTITION in self.partitions:
              for SELF_ADAPTIVE in self.self_adaptives:
                for DATASET in self.datasets:
                  for SHUTDOWN in self.shutdowns:
                    for QUANTIZATIONS in self.quantizations:
                      for TM_ALPHA in self.tm_alpha:
                        for TM_GAMMA in self.tm_gamma:
                          for EG_EPISLON in self.eg_epsilon:
                            for EG_DECAY in self.eg_decay:
                              for EG_MINIMUM in self.eg_minimum:
                                for NN_DETERMINISTIC in self.nn_deterministic:
                                  for NN_BUFFER_SIZE in self.nn_buffer_size:
                                    self.archive.switch(Configuration(agent=AGENT,
                                                                      observation=OBSERVATION,
                                                                      reward=REWARD,
                                                                      partition=PARTITION,
                                                                      self_adaptive=SELF_ADAPTIVE,
                                                                      dataset=DATASET,
                                                                      shutdown=SHUTDOWN,
                                                                      quantization=QUANTIZATIONS,
                                                                      tm_alpha=TM_ALPHA,
                                                                      tm_gamma=TM_GAMMA,
                                                                      eg_epsilon=EG_EPISLON,
                                                                      eg_decay=EG_DECAY,
                                                                      eg_minimum=EG_MINIMUM,
                                                                      nn_deterministic=NN_DETERMINISTIC,
                                                                      nn_buffer_size=NN_BUFFER_SIZE))
                                    args = ['python', '-m', 'main', '-r', '-DT', '-S', str(seed)]
                                    args += self.archive.config.to_cli()
                                    exec_cmd(' '.join(args))
                                    #exec_cmd('python -m tools.plot2')

  def evaluation(self):
    for i in use_iterations(5):
      seed = random.randint(0, 10000)
      for AGENT in self.agents:
        for OBSERVATION in self.observations:
          for REWARD in self.rewards:
            for PARTITION in self.partitions:
              for SELF_ADAPTIVE in self.self_adaptives:
                for DATASET in self.datasets:
                  for SHUTDOWN in self.shutdowns:
                    for QUANTIZATIONS in self.quantizations:
                      for TM_ALPHA in self.tm_alpha:
                        for TM_GAMMA in self.tm_gamma:
                          for EG_EPISLON in self.eg_epsilon:
                            for EG_DECAY in self.eg_decay:
                              for EG_MINIMUM in self.eg_minimum:
                                for NN_DETERMINISTIC in self.nn_deterministic:
                                  for NN_BUFFER_SIZE in self.nn_buffer_size:
                                    self.archive.switch(Configuration(agent=AGENT,
                                                                      observation=OBSERVATION,
                                                                      reward=REWARD,
                                                                      partition=PARTITION,
                                                                      self_adaptive=SELF_ADAPTIVE,
                                                                      dataset=DATASET,
                                                                      shutdown=SHUTDOWN,
                                                                      quantization=QUANTIZATIONS,
                                                                      tm_alpha=TM_ALPHA,
                                                                      tm_gamma=TM_GAMMA,
                                                                      eg_epsilon=EG_EPISLON,
                                                                      eg_decay=EG_DECAY,
                                                                      eg_minimum=EG_MINIMUM,
                                                                      nn_deterministic=NN_DETERMINISTIC,
                                                                      nn_buffer_size=NN_BUFFER_SIZE))
                                    args = ['python', '-m', 'main', '-r', '-DE', '-S', str(seed)]
                                    args += self.archive.config.to_cli()
                                    exec_cmd(' '.join(args))
                                    exec_cmd('python -m tools.extract-global-metrics')
      exec_cmd('python -m tools.compare-global-metrics')
      exec_cmd('mv scores.csv experiments/%s/rounds/%s.csv' % (self.id, i))

  def pack(self):
    exec_cmd('tar cvf ./experiments/%s/rounds.tar experiments/%s/rounds' % (self.id, self.id))
    exec_cmd('tar cvf ./experiments/%s.tar experiments/%s' % (self.id, self.id))
    exec_cmd('zstd ./experiments/%s.tar' % (self.id))

  def clean(self):
    exec_cmd('rm -rf ./archive')
    exec_cmd('rm -rf ./experiments/%s.tar' % (self.id))
    exec_cmd('rm -rf ./experiments/%s/rounds.tar' % (self.id))

  def commit(self):
    exec_cmd('git add ./experiments/%s.tar.zst' % (self.id))
    exec_cmd('git commit -m "Autocommit for JOB of Experiment %s!"' % (self.id))
    exec_cmd('git push')
