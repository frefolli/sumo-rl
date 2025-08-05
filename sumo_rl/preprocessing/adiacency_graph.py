from sumo_rl.environment.env import SumoEnvironment
from sumo_rl.preprocessing.graphs import Graph

def build_adiacency_graph(env: SumoEnvironment, graph: Graph|None = None) -> Graph:
  if graph is None:
    graph = Graph()
  traffic_signals = list(env.traffic_signals.keys())
  for traffic_signal in traffic_signals:
    graph.nodes[traffic_signal] = env.traffic_signals[traffic_signal]
  edges = env.sumo.edge.getIDList()
  for edge_ID in edges:
    from_junction = env.sumo.edge.getFromJunction(edge_ID)
    to_junction = env.sumo.edge.getToJunction(edge_ID)
    if from_junction in traffic_signals and  to_junction in traffic_signals and from_junction != to_junction:
        graph.add_symmetric_edge(from_junction, to_junction)
  return graph
