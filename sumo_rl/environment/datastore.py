class Datastore:
  def __init__(self) -> None:
    self.lanes: dict[str, dict] = {}
    self.vehicles: dict[str, dict] = {}
    self.reward_cache: dict[str, dict] = {}
    self.observation_cache: dict[str, dict] = {}
