#!/usr/bin/env python3
from __future__ import annotations
import sumo_rl.models.sumo
from sumo_rl.models.commons import Point

"""
# Topologic Generator

## Simple Linear
     |  |  |
-> ==+==+==+==
     |  |  |

number_of_junctions = () => rand(X / 2, 2 * X)
edge_length = () => rand(Y / 2, 2 * Y)
// Branches
lane_number = () => prog_rand(1, Z)
// Main line
lane_number = Z

## Simple Rad
     |  |
   --+--+--+--
     |     |
-> --+

prob_gen_branch = () => binomial(X)
edge_length = () => rand(Y / 2, 2 * Y)
lane_number = () => prog_rand(1, Z)
"""

class Node:
  def __init__(self, id: int, point: Point) -> None:
    self.id = id
    self.point: Point = point

  def getID(self) -> str:
    return "N_%s" % (self.id)

  def iedgeID(self, edge_idx: int) -> str:
    return "N_%s_%s" % (self.id, edge_idx)

  def ilaneID(self, edge_idx: int, lane_idx: int) -> str:
    return "N_%s_%s_%s" % (self.id, edge_idx, lane_idx)

class Edge:
  def __init__(self, source: Node, target: Node, number_of_lanes: int) -> None:
    self.source = source
    self.target = target
    self.number_of_lanes: int = number_of_lanes

  def getID(self) -> str:
    return "E_%s_%s" % (self.source.id, self.target.id)

  def laneID(self, lane_num: int) -> str:
    assert lane_num < self.number_of_lanes
    return "E_%s_%s_%s" % (self.source.id, self.target.id, lane_num)

class Topology:
  def __init__(self) -> None:
    self.nodes: dict[int, Node] = {}
    self.forward_edges: dict[int, dict[int, Edge]] = {}
    self.backward_edges: dict[int, dict[int, Edge]] = {}

  def next_node_ID(self) -> int:
    return len(self.nodes)

  def add_node(self, a: Node) -> Node:
    self.nodes[a.id] = a
    return a

  def double_link(self, a: Node, b: Node, number_of_lanes: int):
    atob = Edge(a, b, number_of_lanes)
    btoa = Edge(b, a, number_of_lanes)
    if a.id not in self.forward_edges:
      self.forward_edges[a.id] = {}
    if b.id not in self.forward_edges:
      self.forward_edges[b.id] = {}
    if a.id not in self.backward_edges:
      self.backward_edges[a.id] = {}
    if b.id not in self.backward_edges:
      self.backward_edges[b.id] = {}
    self.forward_edges[a.id][b.id] = atob
    self.backward_edges[b.id][a.id] = atob
    self.forward_edges[b.id][a.id] = btoa
    self.backward_edges[a.id][b.id] = btoa

def generate_simple_linear() -> Topology:
  pass

def generate_simple_rad() -> Topology:
  pass

def realize_edge(edge: Edge) -> sumo_rl.models.sumo.Edge:
  lanes = []
  for i in range(edge.number_of_lanes):
    lanes.append(sumo_rl.models.sumo.Lane(edge.laneID(i), i, 13.0, edge.source.point.distance(edge.target.point), shape=[edge.source.point, edge.target.point]))
  return sumo_rl.models.sumo.Edge(edge.getID(), edge.source.getID(), edge.target.getID(), shape=[edge.source.point, edge.target.point], lanes=lanes)

NODE_BUILDER_YIELD=tuple[sumo_rl.models.sumo.Junction, list[sumo_rl.models.sumo.ViaConnection], list[sumo_rl.models.sumo.InternalConnection], list[sumo_rl.models.sumo.InternalEdge], list[sumo_rl.models.sumo.TLLogic]]
def realize_node_as_dead_end(topology: Topology, node: Node) -> NODE_BUILDER_YIELD:
  outgoing_edges = topology.forward_edges[node.id]
  ingoing_edges = topology.backward_edges[node.id]

  outgoing_lanes = [edge.laneID(lane_idx) for edge in outgoing_edges.values() for lane_idx in range(edge.number_of_lanes)]
  ingoing_lanes = [edge.laneID(lane_idx) for edge in ingoing_edges.values() for lane_idx in range(edge.number_of_lanes)]

  junction = sumo_rl.models.sumo.Junction(node.getID(), 'dead_end', node.point, ingoing_lanes, outgoing_lanes, [])
  return junction, [], [], [], []

def realize_node_as_priority(topology: Topology, node: Node) -> NODE_BUILDER_YIELD:
  outgoing_edges = topology.forward_edges[node.id]
  ingoing_edges = topology.backward_edges[node.id]

  outgoing_lanes = [edge.laneID(lane_idx) for edge in outgoing_edges.values() for lane_idx in range(edge.number_of_lanes)]
  ingoing_lanes = [edge.laneID(lane_idx) for edge in ingoing_edges.values() for lane_idx in range(edge.number_of_lanes)]

  junction = sumo_rl.models.sumo.Junction(node.getID(), 'priority', node.point, ingoing_lanes, outgoing_lanes, [])

  via_connections = []
  internal_connections = []
  internal_edges = []

  internal_edges.append(sumo_rl.models.sumo.InternalEdge(node.iedgeID(0), []))
  internal_lanes = []
  for in_edge in ingoing_edges.values():
    for out_edge in outgoing_edges.values():
      idx = len(internal_lanes)
      lane = sumo_rl.models.sumo.Lane(node.ilaneID(0, idx), idx, 5, 5)
      internal_lanes.append(lane)

      for in_lane in range(in_edge.number_of_lanes):
        for out_lane in range(out_edge.number_of_lanes):
          via_connections.append(sumo_rl.models.sumo.ViaConnection(in_edge.getID(), out_edge.getID(), in_lane, out_lane, 's', 0, lane.id, None))
      internal_connections.append(sumo_rl.models.sumo.InternalConnection(internal_edges[-1].id, out_edge.getID(), idx, out_lane, 's'))
  internal_edges[-1].lanes = internal_lanes
  return junction, via_connections, internal_connections, internal_edges, []

def realize_node(topology: Topology, node: Node) -> NODE_BUILDER_YIELD:
  outgoing_edges = topology.forward_edges[node.id]
  ingoing_edges = topology.backward_edges[node.id]
  if len(outgoing_edges) == 1 and len(ingoing_edges) == 1:
    return realize_node_as_dead_end(topology, node)
  else:
    return realize_node_as_priority(topology, node)

def realize_topology(topology: Topology) -> sumo_rl.models.sumo.Network:
  road_edges: list[sumo_rl.models.sumo.Edge] = []

  for fromA in topology.forward_edges.values():
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

def stub_topology():
  topology = Topology()
  A = topology.add_node(Node(topology.next_node_ID(), Point(0, 0)))
  B = topology.add_node(Node(topology.next_node_ID(), Point(100, 0)))
  C = topology.add_node(Node(topology.next_node_ID(), Point(200, 0)))
  D = topology.add_node(Node(topology.next_node_ID(), Point(100, 100)))
  E = topology.add_node(Node(topology.next_node_ID(), Point(100, -100)))
  topology.double_link(A, B, 2)
  topology.double_link(B, C, 2)
  topology.double_link(D, B, 2)
  topology.double_link(E, B, 2)
  return topology

if __name__ == "__main__":
  topology = stub_topology()
  network = realize_topology(topology)
  print(network)
