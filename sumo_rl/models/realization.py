"""
Topology Realization
"""
import sumo_rl.models.sumo
import sumo_rl.models.topology
import math

def balance_branches(lhs: list, rhs: list) -> tuple[list, list]:
  while abs(len(lhs) - len(rhs)) > 1:
    if len(lhs) - len(rhs) > 1:
      rhs = rhs + [lhs[0]]
      lhs = lhs[1:]
    elif len(rhs) - len(lhs) > 1:
      lhs = [rhs[-1]] + lhs
      rhs = rhs[:-1]
  return lhs, rhs

def realize_edge(edge: sumo_rl.models.topology.Edge) -> sumo_rl.models.sumo.Edge:
  lanes = []
  for i in range(edge.number_of_lanes):
    lanes.append(sumo_rl.models.sumo.Lane(edge.laneID(i), i, 13.0, edge.source.point.distance(edge.target.point), shape=[edge.source.point, edge.target.point]))
  return sumo_rl.models.sumo.Edge(edge.getID(), edge.source.getID(), edge.target.getID(), shape=[edge.source.point, edge.target.point], lanes=lanes)

def partition_lanes(in_edge: sumo_rl.models.topology.Edge, outgoing_edges: list[sumo_rl.models.topology.Edge]) -> list[tuple[tuple[sumo_rl.models.topology.Edge, int], list[tuple[sumo_rl.models.topology.Edge, int]]]]:
  rank = [(edge, edge.source.point.direction(edge.target.point)) for edge in outgoing_edges]
  rank = sorted(rank, key=lambda e: e[1])

  # factor = in_edge.source.point.direction(in_edge.target.point)
  factor = in_edge.target.point.direction(in_edge.source.point)

  lhs = list(filter(lambda e: e[1] <= factor, rank))
  rhs = list(filter(lambda e: e[1] > factor, rank))
  lhs, rhs = balance_branches(lhs, rhs)
  rank = lhs + rhs

  # print(in_edge, outgoing_edges, lhs, rhs)

  lanes_to_partition = [(out_edge[0], idx) for out_edge in lhs for idx in range(out_edge[0].number_of_lanes)]
  lanes_to_partition += [(out_edge[0], idx) for out_edge in rhs for idx in range(out_edge[0].number_of_lanes)][::-1]
  lanes_to_partition = lanes_to_partition
  partition_heads = [(in_edge, idx) for idx in range(in_edge.number_of_lanes)][::-1]
  
  assert len(lanes_to_partition) > len(partition_heads)
  k = math.ceil(len(lanes_to_partition) / len(partition_heads))

  partitions = []
  for part_idx in range(len(partition_heads)):
    lb, hb = k * part_idx, k * (part_idx + 1)
    partitions.append((partition_heads[part_idx], lanes_to_partition[lb:hb]))
  diff = len(lanes_to_partition) - sum([len(part[1]) for part in partitions])
  if diff > 0:
    partitions[-1] = (partitions[-1][0], partitions[-1][1] + lanes_to_partition[-diff:])
  return partitions

NODE_BUILDER_YIELD=tuple[sumo_rl.models.sumo.Junction,
                         list[sumo_rl.models.sumo.ViaConnection],
                         list[sumo_rl.models.sumo.InternalConnection],
                         list[sumo_rl.models.sumo.InternalEdge],
                         list[sumo_rl.models.sumo.TLLogic]]
def realize_node_as_dead_end(topology: sumo_rl.models.topology.Topology, node: sumo_rl.models.topology.Node) -> NODE_BUILDER_YIELD:
  outgoing_edges = list(topology.outgoing_edges[node.id].values())
  ingoing_edges = list(topology.ingoing_edges[node.id].values())

  outgoing_lanes = [edge.laneID(lane_idx) for edge in outgoing_edges for lane_idx in range(edge.number_of_lanes)]
  ingoing_lanes = [edge.laneID(lane_idx) for edge in ingoing_edges for lane_idx in range(edge.number_of_lanes)]

  junction = sumo_rl.models.sumo.Junction(node.getID(), 'dead_end', node.point, ingoing_lanes, outgoing_lanes, [])
  via_connections: list[sumo_rl.models.sumo.ViaConnection] = []
  internal_connections: list[sumo_rl.models.sumo.InternalConnection] = []
  internal_edges: list[sumo_rl.models.sumo.InternalEdge] = []
  tl_logics: list[sumo_rl.models.sumo.TLLogic] = []
  return junction, via_connections, internal_connections, internal_edges, tl_logics

def realize_node_as_priority(topology: sumo_rl.models.topology.Topology, node: sumo_rl.models.topology.Node) -> NODE_BUILDER_YIELD:
  junction, via_connections, internal_connections, internal_edges, tl_logics = realize_node_as_dead_end(topology, node)
  junction.kind = 'priority'
  ingoing_edges = list(topology.ingoing_edges[node.id].values())

  internal_edges.append(sumo_rl.models.sumo.InternalEdge(node.iedgeID(0), []))
  internal_lanes: list[sumo_rl.models.sumo.Lane] = []
  for in_edge in ingoing_edges:
    # partition = partition_lanes(in_edge, list(filter(lambda oedge: oedge.target.id != in_edge.source.id, topology.outgoing_edges[node.id].values())))
    partition = partition_lanes(in_edge, list(topology.outgoing_edges[node.id].values()))
    for (in_lane, out_lanes) in partition:
      idx = len(internal_lanes)
      lane = sumo_rl.models.sumo.Lane(node.ilaneID(0, idx), idx, 5, 5)
      internal_lanes.append(lane)
      for out_lane in out_lanes:
        via_connections.append(sumo_rl.models.sumo.ViaConnection(in_lane[0].getID(), out_lane[0].getID(), in_lane[1], out_lane[1], 's', idx, lane.id, None))
        internal_connections.append(sumo_rl.models.sumo.InternalConnection(internal_edges[-1].id, out_lane[0].getID(), idx, out_lane[1], 's'))
  internal_edges[-1].lanes = internal_lanes
  return junction, via_connections, internal_connections, internal_edges, tl_logics

def realize_node_as_traffic_light(topology: sumo_rl.models.topology.Topology, node: sumo_rl.models.topology.Node) -> NODE_BUILDER_YIELD:
  junction, via_connections, internal_connections, internal_edges, tl_logics = realize_node_as_priority(topology, node)
  junction.kind = 'traffic_light'

  for via_connection in via_connections:
    via_connection.junction_id = node.getID()

  phases: list[sumo_rl.models.sumo.Phase] = []
  blocks: dict[str, set[int]] = {}
  for via_connection in via_connections:
    if via_connection.from_edge not in blocks:
      blocks[via_connection.from_edge] = set({})
    blocks[via_connection.from_edge].add(via_connection.index)

  for phase_id in blocks:
    phase = ""
    for v in range(len(internal_edges[0].lanes)):
      if v in blocks[phase_id]:
        phase += 'g'
      else:
        phase += 'r'
    phase_2 = phase.replace("g", "y")
    phases.append(sumo_rl.models.sumo.Phase(30.0, phase))
    phases.append(sumo_rl.models.sumo.Phase(30.0, phase_2))

  tl_logics.append(sumo_rl.models.sumo.TLLogic(node.getID(), phases=phases))
  return junction, via_connections, internal_connections, internal_edges, tl_logics

def realize_node(topology: sumo_rl.models.topology.Topology, node: sumo_rl.models.topology.Node) -> NODE_BUILDER_YIELD:
  outgoing_edges = list(topology.outgoing_edges[node.id].values())
  ingoing_edges = list(topology.ingoing_edges[node.id].values())
  if len(outgoing_edges) == 1 and len(ingoing_edges) == 1:
    return realize_node_as_dead_end(topology, node)
  else:
    # return realize_node_as_priority(topology, node)
    return realize_node_as_traffic_light(topology, node)

def realize_topology(topology: sumo_rl.models.topology.Topology) -> sumo_rl.models.sumo.Network:
  road_edges: list[sumo_rl.models.sumo.Edge] = []

  for fromA in topology.outgoing_edges.values():
    for toB in fromA.values():
      road_edges.append(realize_edge(toB))

  junctions: list[sumo_rl.models.sumo.Junction] = []
  via_connections: list[sumo_rl.models.sumo.ViaConnection] = []
  internal_connections: list[sumo_rl.models.sumo.InternalConnection] = []
  internal_edges: list[sumo_rl.models.sumo.InternalEdge] = []
  tllogics: list[sumo_rl.models.sumo.TLLogic] = []

  for node in topology.nodes.values():
    _j, _vc, _ic, _ie, _tl = realize_node(topology, node)
    junctions.append(_j)
    via_connections += _vc
    internal_connections += _ic
    internal_edges += _ie
    tllogics += _tl

  return sumo_rl.models.sumo.Network(road_edges, junctions, via_connections, internal_connections, internal_edges, tllogics)


