"""
Topology Data Structures
"""
from __future__ import annotations
from sumo_rl.models.commons import Point
from sumo_rl.models.serde import SerdeDict, SerdeJsonFile

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

  def __repr__(self) -> str:
    return "(%s)" % (self.point)

  def to_dict(self) -> dict:
    return {
      'id': self.id,
      'point': self.point.to_dict()
    }

class Edge:
  def __init__(self, source: Node, target: Node, number_of_lanes: int) -> None:
    self.source = source
    self.target = target
    self.number_of_lanes: int = number_of_lanes

  def getID(self) -> str:
    id = "E_%s_%s" % (self.source.id, self.target.id)
    if self.source.id < self.target.id:
      id = "-" + id
    return id

  def laneID(self, lane_num: int) -> str:
    assert lane_num < self.number_of_lanes
    return "%s_%s" % (self.getID(), lane_num)

  def shape(self) -> tuple[Point, Point]:
    return (self.source.point, self.target.point)

  def __repr__(self) -> str:
    return "%s -> %s" % (self.source, self.target)

  def to_dict(self) -> dict:
    return {
      'source': self.source.id,
      'target': self.target.id,
      'number_of_lanes': self.number_of_lanes
    }

class Topology(SerdeJsonFile):
  def __init__(self) -> None:
    self.nodes: dict[int, Node] = {}
    self.outgoing_edges: dict[int, dict[int, Edge]] = {}
    self.ingoing_edges: dict[int, dict[int, Edge]] = {}

  def next_node_ID(self) -> int:
    return len(self.nodes)

  def add_node(self, a: Node) -> Node:
    self.nodes[a.id] = a
    return a

  def double_link(self, a: Node, b: Node, number_of_lanes: int):
    atob = Edge(a, b, number_of_lanes)
    btoa = Edge(b, a, number_of_lanes)
    if a.id not in self.outgoing_edges:
      self.outgoing_edges[a.id] = {}
    if b.id not in self.outgoing_edges:
      self.outgoing_edges[b.id] = {}
    if a.id not in self.ingoing_edges:
      self.ingoing_edges[a.id] = {}
    if b.id not in self.ingoing_edges:
      self.ingoing_edges[b.id] = {}
    self.outgoing_edges[a.id][b.id] = atob
    self.ingoing_edges[b.id][a.id] = atob
    self.outgoing_edges[b.id][a.id] = btoa
    self.ingoing_edges[a.id][b.id] = btoa
  
  def to_dict(self) -> dict:
    return {
      'nodes': [
        node.to_dict()
        for node in self.nodes.values()
      ],
      'edges': [
        edge.to_dict()
        for edge_set in self.outgoing_edges.values()
        for edge in edge_set.values()
      ]
    }
  
  @staticmethod
  def from_dict(data: dict) -> Topology:
    topology = Topology()
    for node in data['nodes']:
      id = node['id']
      point = Point(node['point']['x'], node['point']['y'])
      topology.add_node(Node(id, point))
    for edge in data['edges']:
      source = topology.nodes[edge['source']]
      target = topology.nodes[edge['target']]
      number_of_lanes = edge['number_of_lanes']
      edge = Edge(source, target, number_of_lanes)

      if source.id not in topology.outgoing_edges:
        topology.outgoing_edges[source.id] = {}
      if target.id not in topology.ingoing_edges:
        topology.ingoing_edges[target.id] = {}
      topology.outgoing_edges[source.id][target.id] = edge
      topology.ingoing_edges[target.id][source.id] = edge
    return topology

  def clear(self):
    self.nodes = {}
    self.outgoing_edges = {}
    self.ingoing_edges = {}


