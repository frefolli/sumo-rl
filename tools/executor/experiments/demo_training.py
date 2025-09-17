from tools.executor.experiments.serial_experiment import SerialExperiment
from tools.executor.archive import Archive, Configuration

def craft(**kwargs):
  return Configuration.Patch(Configuration.Default(), dataset='curriculum_daily_plus_disruption', **kwargs)

class DemoTraining(SerialExperiment):
  def __init__(self, archive: Archive) -> None:
    super().__init__("DT", "DemoTraining", archive, skip_cleaning=True, skip_evaluation=True)
    self.configurations = [
      craft(agent='dql', observation='d', reward='dwt'),
      craft(agent='dql', observation='svp', reward='svdwt'),
      craft(agent='ppo', observation='d', reward='dwt'),
      craft(agent='fixed15'),
      craft(shutdown=True),
    ]
