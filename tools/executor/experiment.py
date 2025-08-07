from tools.executor.archive import Archive

class Experiment:
  def __init__(self, id: str, name: str, archive: Archive, skip_training: bool = False) -> None:
    self.archive = archive
    self.id = id
    self.name = name
    self.skip_training = skip_training

  def all(self):
    self.prepare()
    if not self.skip_training:
      self.training()
    self.evaluation()
    self.pack()
    self.clean()

  def prepare(self):
    """Prepare for experiment"""
    pass

  def training(self):
    """Train the agents"""
    pass

  def evaluation(self):
    """Evaluate the agents"""
    pass

  def pack(self):
    """Pack results"""
    pass

  def clean(self):
    """Clean up"""
    pass

  def commit(self):
    """Send results package to Git"""
    pass
