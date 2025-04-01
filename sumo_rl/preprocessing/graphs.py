from sumo_rl.environment.traffic_signal import TrafficSignal
import sumo_rl.models.serde
import sumo_rl.models.commons

class Graph(sumo_rl.models.serde.SerdeD2File):
  def __init__(self) -> None:
    self.edges: dict[str, set[str]] = {}
    self.nodes: dict[str, TrafficSignal] = {}

  def add_asymmetric_edge(self, from_ID: str, to_ID: str):
    if from_ID not in self.edges:
      self.edges[from_ID] = set({})
    if to_ID not in self.edges[from_ID]:
      self.edges[from_ID].add(to_ID)

  def add_symmetric_edge(self, from_ID: str, to_ID: str):
    self.add_asymmetric_edge(from_ID, to_ID)
    self.add_asymmetric_edge(to_ID, from_ID)

  def to_d2(self, indent: int = 0) -> str:
    rep: str = ""
    for ts_ID, ts in self.nodes.items():
      rep += sumo_rl.models.commons.indentation(indent) + '%s: "%s"' % (ts_ID, ts.id) + '\n'
    for ts_A_ID, ts_B_IDs in self.edges.items():
      for ts_B_ID in ts_B_IDs:
        rep += sumo_rl.models.commons.indentation(indent) + '%s -> %s' % (ts_A_ID, ts_B_ID) + '\n'
    return rep
