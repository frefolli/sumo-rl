from sumo_rl.models.commons import Point, parse_shape
import sumo_rl.models.sumo
import xml.etree.ElementTree as ET
import os
import sumo_rl.models.serde

MIN_GAP = 2.5
VEHICLE_LENGTH = 5.0
TAU = 1.0

class DeadEnd:
  def __init__(self, id: str) -> None:
    self.id: str = id

  def __repr__(self) -> str:
    return '<%s>' % self.id

class Lane:
  def __init__(self, length: float, speed: float) -> None:
    self.length: float = length
    self.speed: float = speed

  @property
  def flow_capacity(self) -> int:
    gross_time_headway = (VEHICLE_LENGTH + MIN_GAP) / (self.speed / 3) + TAU
    lane_capacity = 3600 / gross_time_headway
    return int(lane_capacity)

  @property
  def queue_capacity(self) -> int:
    lane_capacity = self.length / (VEHICLE_LENGTH + MIN_GAP)
    return int(lane_capacity)

class Edge:
  def __init__(self, id: str, from_junction: str, to_junction: str, lanes: list[Lane], shape: list[Point]) -> None:
    self.id: str = id
    self.from_junction: str = from_junction
    self.to_junction: str = to_junction
    self.lanes: list[Lane] = lanes
    self.shape: list[Point] = shape

  @property
  def flow_capacity(self) -> int:
    return sum([lane.flow_capacity for lane in self.lanes])

  @property
  def queue_capacity(self) -> int:
    return sum([lane.queue_capacity for lane in self.lanes])

  def __repr__(self) -> str:
    return "%s -> %s" % (self.from_junction, self.to_junction)

class Flow(sumo_rl.models.sumo.JunctionFlow):
  INCREMENTAL_IDX = 0
  @staticmethod
  def nextID() -> str:
    id = Flow.INCREMENTAL_IDX
    Flow.INCREMENTAL_IDX += 1
    return 'JF' + str(id)

  def change_begin(self, new_begin: int):
    assert new_begin >= 0
    duration = self.end - self.begin
    new_end = new_begin + duration
    self.begin, self.end = new_begin, new_end

  def change_end(self, new_end: int):
    duration = self.end - self.begin
    new_begin = new_end - duration
    assert new_begin >= 0
    self.begin, self.end = new_begin, new_end

  def change_duration(self, new_duration: int):
    assert new_duration >= 0
    new_end = self.begin + new_duration
    self.end = new_end

  def relocate(self, delta_time: int):
    new_begin = self.begin + delta_time
    assert new_begin >= 0
    self.change_begin(new_begin)

  def __repr__(self) -> str:
    return self.to_xml()

class Flows:
  def __init__(self, flows: list[Flow]) -> None:
    self.flows = flows

  def concat(self, flows: list[Flow]) -> None:
    end = self.get_end()
    for flow in flows:
      flow.relocate(end)
    self.flows += flows

  def get_end(self) -> int:
    end = 0
    for flow in self.flows:
      if flow.end > end:
        end = flow.end
    return end

  def unpack(self) -> list[Flow]:
    return self.flows

class Axis:
  def __init__(self, A: DeadEnd, B: DeadEnd) -> None:
    self.A: DeadEnd = A
    self.B: DeadEnd = B

  def __repr__(self) -> str:
    return "<%s - %s>" % (self.A.id, self.B.id)

class Layout:
  def __init__(self, main_axes: list[Axis], side_axes: list[Axis]) -> None:
    self.main_axes = main_axes
    self.side_axes = side_axes

  def main_dead_ends(self) -> set[DeadEnd]:
    dead_ends = set({})
    for axis in self.main_axes:
      dead_ends.add(axis.A)
      dead_ends.add(axis.B)
    return dead_ends

  def side_dead_ends(self) -> set[DeadEnd]:
    dead_ends = set({})
    for axis in self.side_axes:
      dead_ends.add(axis.A)
      dead_ends.add(axis.B)
    return dead_ends

class Network:
  def __init__(self, dead_ends: dict[str, DeadEnd], edges: list[Edge], layout: Layout = Layout([], [])) -> None:
    self.dead_ends: dict[str, DeadEnd] = dead_ends
    self.edges: list[Edge] = edges
    self.layout: Layout = layout

  @staticmethod
  def Load(basepath: str):
    network_file = os.path.join(basepath, 'network.net.xml')

    tree = ET.parse(network_file)
    xml_root = tree.getroot()
    dead_ends = {}
    for child in xml_root:
      if child.tag == 'junction':
        if child.attrib['type'] == 'dead_end':
          id = child.attrib['id']
          dead_ends[id] = DeadEnd(id)

    edges = []
    for child in xml_root:
      if child.tag == 'edge':
        if 'function' not in child.attrib:
          if 'shape' not in child.attrib:
            raise ValueError(child.attrib)
          edges.append(Edge(child.attrib['id'], child.attrib['from'], child.attrib['to'], [
            Lane(float(lane.attrib['length']), float(lane.attrib['speed']))
            for lane in child
            if ('allow' not in lane.attrib or lane.attrib['allow'] in ['all'])
            ], parse_shape(child.attrib['shape'])))

    config_file = os.path.join(basepath, 'config.yml')
    config = sumo_rl.models.serde.GenericFile.from_yaml_file(config_file).data
    assert 'layout' in config
    assert 'main' in config['layout']
    assert 'side' in config['layout']

    dead_end_seen = {dead_end:False for dead_end in dead_ends.keys()}
    axis_seen = {}

    main_axes = []

    def extract_axes_from_layout(config_axes: dict):
      axes = []
      for axis in config_axes:
        assert 'A' in axis
        assert 'B' in axis
        A = axis['A']
        B = axis['B']
        assert A in dead_ends
        assert B in dead_ends
        dead_end_seen[A] = True
        dead_end_seen[B] = True
        assert (A, B) not in axis_seen
        assert (B, A) not in axis_seen
        axes.append(Axis(dead_ends[A], dead_ends[B]))
        axis_seen[(A, B)] = True
      return axes

    main_axes = extract_axes_from_layout(config['layout']['main'])
    side_axes = extract_axes_from_layout(config['layout']['side'])

    for (dead_end, has_be_seen) in dead_end_seen.items():
      if not has_be_seen:
        raise ValueError('dead_end %s has not be seen in any Axis' % dead_end)
    layout = Layout(main_axes, side_axes)

    return Network(dead_ends, edges, layout)

  @property
  def positions(self) -> dict[str, Point]:
    positions: dict[str, Point] = {}
    for edge in self.edges:
      positions[edge.from_junction] = edge.shape[0]
      positions[edge.to_junction] = edge.shape[-1]
    return positions

  @property
  def flow_capacities(self) -> dict[str, int]:
    capacities: dict[str, int] = {}
    for edge in self.edges:
      if edge.from_junction in self.dead_ends:
        if edge.from_junction not in capacities:
          capacities[edge.from_junction] = 0
        capacities[edge.from_junction] += edge.flow_capacity
    return capacities

  @property
  def queue_capacities(self) -> dict[str, int]:
    capacities: dict[str, int] = {}
    for edge in self.edges:
      if edge.from_junction in self.dead_ends:
        if edge.from_junction not in capacities:
          capacities[edge.from_junction] = 0
        capacities[edge.from_junction] += edge.queue_capacity
    return capacities

  @property
  def flow_capacity(self) -> int:
    return sum([
      lane.flow_capacity
      for edge in self.edges
      for lane in edge.lanes
      if (edge.from_junction in self.dead_ends or edge.to_junction in self.dead_ends)
    ])

  @property
  def queue_capacity(self) -> int:
    return sum([lane.queue_capacity for edge in self.edges for lane in edge.lanes])

def read_flows_from_routes_file(filepath: str) -> dict[str, str]:
  tree = ET.parse(filepath)
  root = tree.getroot()
  result = {}
  for child in root:
    assert child.tag == 'flow'
    (flow_id, flow_dir) = (child.attrib['id'], "%s-%s" % (child.attrib['fromJunction'], child.attrib['toJunction']))
    result[flow_id] = flow_dir
  return result

def read_flows_with_occupancy_from_routes_file(filepath: str) -> dict[str, dict]:
  tree = ET.parse(filepath)
  root = tree.getroot()
  result = {}
  for child in root:
    assert child.tag == 'flow'
    result[child.attrib['id']] = {
      'from': child.attrib['fromJunction'],
      'to': child.attrib['toJunction'],
      'vehs': float(child.attrib['vehsPerHour']),
      'begin': int(child.attrib['begin']),
      'end': int(child.attrib['end'])
    }
  return result
