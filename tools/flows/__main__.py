"""
Sogno tecnologico bolscevico
Atea mistica meccanica
Macchina automatica. No anima
"""

from typing import Generator
import xml.etree.ElementTree as ET
import sumo_rl.models.sumo
import argparse
import sys
import random
import os

MIN_GAP = 2.5
VEHICLE_LENGTH = 5.0
TAU = 1.0
random.seed(170701)

def is_reverse_of(A_id: str, B_id: str) -> bool:
  if A_id == '-' + B_id:
    return True
  if '-' + A_id == B_id:
    return True
  return False

class DeadEnd:
  def __init__(self, id: str) -> None:
    self.id: str = id

  def __repr__(self) -> str:
    return self.id

class Lane:
  def __init__(self, length: float, speed: float) -> None:
    self.length: float = length
    self.speed: float = speed

  def flow_capacity(self) -> int:
    gross_time_headway = (VEHICLE_LENGTH + MIN_GAP) / (self.speed / 3) + TAU
    lane_capacity = 3600 / gross_time_headway
    return int(lane_capacity)

  def queue_capacity(self) -> int:
    lane_capacity = self.length / (VEHICLE_LENGTH + MIN_GAP)
    return int(lane_capacity)

class Edge:
  def __init__(self, id: str, from_junction: str, to_junction: str, lanes: list[Lane]) -> None:
    self.id: str = id
    self.from_junction: str = from_junction
    self.to_junction: str = to_junction
    self.lanes: list[Lane] = lanes

  def flow_capacity(self) -> int:
    return sum([lane.flow_capacity() for lane in self.lanes])

  def queue_capacity(self) -> int:
    return sum([lane.queue_capacity() for lane in self.lanes])

  def __repr__(self) -> str:
    return "%s -> %s" % (self.from_junction, self.to_junction)

FLOW_IDX = 0
class Flow(sumo_rl.models.sumo.JunctionFlow):
  @staticmethod
  def nextID() -> str:
    global FLOW_IDX
    id = FLOW_IDX
    FLOW_IDX += 1
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

  def __repr__(self) -> str:
    return self.to_xml()
    return "%s -> %s :: %s" % (self.fromJunction, self.toJunction, self.vehsPerHour)

def acquire_dead_ends(xml_root) -> list[DeadEnd]:
  dead_ends = []
  for child in xml_root:
    if child.tag == 'junction':
      if child.attrib['type'] == 'dead_end':
        dead_ends.append(DeadEnd(child.attrib['id']))
  return dead_ends

def acquire_edges(xml_root) -> list[Edge]:
  edges = []
  for child in xml_root:
    if child.tag == 'edge':
      if 'function' not in child.attrib:
        edges.append(Edge(child.attrib['id'], child.attrib['from'], child.attrib['to'], [
          Lane(float(lane.attrib['length']), float(lane.attrib['speed']))
          for lane in child
          if ('allow' not in lane.attrib or lane.attrib['allow'] in ['all'])
        ]))
  return edges

def compute_flow_capacity_in_vehicles_per_hour(dead_ends: list[DeadEnd], edges: list[Edge]) -> int:
  dead_end_map = {dead_end.id:dead_end for dead_end in dead_ends}
  return sum([
    lane.flow_capacity()
    for edge in edges
    for lane in edge.lanes
    if (edge.from_junction in dead_end_map or edge.to_junction in dead_end_map)
  ])

def compute_queue_capacity_in_vehicles_per_hour(edges: list[Edge]) -> int:
  return sum([lane.queue_capacity() for edge in edges for lane in edge.lanes])

def extract_at_random(pickables: list, amount_to_extract: int) -> tuple[list, list]:
  assert amount_to_extract < len(pickables)
  picked = []
  for _ in range(amount_to_extract):
    i = random.randint(0, len(pickables) - 1)
    picked.append(pickables[i])
    pickables = pickables[:i] + pickables[i + 1:]
  return picked, pickables

def extract_all_combs(pickables: list, amount_to_extract: int) -> Generator[tuple[list, list], None, None]:
  if len(pickables) == 0 or amount_to_extract == 0:
    yield [], pickables
  elif len(pickables) == amount_to_extract:
    yield pickables, []
  else:
    el = pickables[0]
    for (yes, no) in extract_all_combs(pickables[1:], amount_to_extract - 1):
      yield (yes + [el], no)
    for (yes, no) in extract_all_combs(pickables[1:], amount_to_extract):
      yield (yes, no + [el])

def assign_flows(traffic_caps: dict[str, int], headings: dict[str, list[tuple[tuple[DeadEnd, DeadEnd], bool]]]):
  LOW_TRAFFIC_CAP_PER = 0.2
  HIGH_TRAFFIC_CAP_PER = 1.0
  LOW_TRAFFIC_WEIGHT_PER = 0.2
  HIGH_TRAFFIC_WEIGHT_PER = 0.8

  flows = []
  for dead_end_id, directions in headings.items():
    has_high_direction = (len([1 for direction in directions if direction[1] == True]))
    traffic_cap: int
    if has_high_direction:
      traffic_cap = traffic_caps[dead_end_id] * HIGH_TRAFFIC_CAP_PER
    else:
      traffic_cap = traffic_caps[dead_end_id] * LOW_TRAFFIC_CAP_PER
    weights = [HIGH_TRAFFIC_WEIGHT_PER if direction[1] else LOW_TRAFFIC_WEIGHT_PER for direction in directions]
    sum_of_weights = sum(weights)
    shares = [weight / sum_of_weights for weight in weights]

    for direction, share in zip(directions, shares):
      flows.append(Flow(Flow.nextID(), 0, 3600, direction[0][0], direction[0][1], share * traffic_cap))
  return flows

def prepare_data_for_flow_design(dead_ends: list[DeadEnd], edges: list[Edge], number_of_busy_directions: int = None, high_traffic_ratio: float = None):
  dead_end_map = {dead_end.id:dead_end for dead_end in dead_ends}
  dead_end_edges_map = {}
  for edge in edges:
    if edge.from_junction in dead_end_map:
      if edge.from_junction not in dead_end_edges_map:
        dead_end_edges_map[edge.from_junction] = []
      dead_end_edges_map[edge.from_junction].append(edge)
  directions = [
    (dead_end_A, dead_end_B)
    for dead_end_A in dead_ends
    for dead_end_B in dead_ends
    if dead_end_A != dead_end_B
  ]

  assert high_traffic_ratio is not None or number_of_busy_directions is not None
  assert high_traffic_ratio is None or number_of_busy_directions is None

  if high_traffic_ratio is not None:
    assert high_traffic_ratio >= 0.0 and high_traffic_ratio <= 1.0
    number_of_busy_directions = int(len(directions) * high_traffic_ratio)
  return directions, number_of_busy_directions, dead_end_edges_map

def execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions):
  traffic_caps = {
    de_id: sum([
      de_edge.flow_capacity()
      for de_edge in de_edges
    ])
    for de_id, de_edges in dead_end_edges_map.items()
  }
  headings = {
    de_id: []
    for de_id in traffic_caps
  }
  for (f, t) in high_traffic_directions:
    headings[f.id].append(((f, t), True))
  for (f, t) in low_traffic_directions:
    headings[f.id].append(((f, t), False))

  return assign_flows(traffic_caps, headings)

def create_random_flow(dead_ends: list[DeadEnd], edges: list[Edge], number_of_busy_directions: int = None, high_traffic_ratio: float = None) -> list[Flow]:
  directions, number_of_busy_directions, dead_end_edges_map = prepare_data_for_flow_design(dead_ends, edges, number_of_busy_directions, high_traffic_ratio)

  high_traffic_directions: list[tuple[DeadEnd, DeadEnd]]
  low_traffic_directions: list[tuple[DeadEnd, DeadEnd]]
  if number_of_busy_directions == 0:
    high_traffic_directions = []
    low_traffic_directions = directions
  elif number_of_busy_directions == len(directions):
    high_traffic_directions = directions
    low_traffic_directions = []
  else:
    high_traffic_directions, low_traffic_directions = extract_at_random(directions, number_of_busy_directions)
  flows = execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions)
  return flows

def create_all_flows(dead_ends: list[DeadEnd], edges: list[Edge], number_of_busy_directions: int = None, high_traffic_ratio: float = None) -> list[Flow]:
  directions, number_of_busy_directions, dead_end_edges_map = prepare_data_for_flow_design(dead_ends, edges, number_of_busy_directions, high_traffic_ratio)

  flows = []
  for (high_traffic_directions, low_traffic_directions) in extract_all_combs(directions, number_of_busy_directions):
    flows.append(execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions))
  return flows

if __name__ == "__main__":
  argument_parser = argparse.ArgumentParser(description='flower')
  argument_parser.add_argument('-s', '--scenario', default='lisca', help='Input scenario')
  argument_parser.add_argument('-oF', '--output-file', default='/tmp/routes.rou.xml', help='Output file')
  argument_parser.add_argument('-oD', '--output-dir', default='output', help='Output directory')
  argument_parser.add_argument('-R', '--random', action='store_true', help='Generates a random routes file')
  argument_parser.add_argument('-C', '--complex', action='store_true', help='Generates a random complex routes file')
  argument_parser.add_argument('-A', '--all', action='store_true', help='Generates all routes files for atomic scenarious saving them as scenarios')
  cli_args = argument_parser.parse_args(sys.argv[1:])

  network_file = "scenarios/%s/network.net.xml" % cli_args.scenario
  tree = ET.parse(network_file)
  xml_root = tree.getroot()

  edges = acquire_edges(xml_root)
  dead_ends = acquire_dead_ends(xml_root)

  if cli_args.random:
    flows = create_random_flow(dead_ends, edges, number_of_busy_directions=1)
    sumo_rl.models.sumo.Routes([], [], [], flows).to_xml_file(cli_args.output_file)
  elif cli_args.complex:
    begin = 0
    duration = 10000
    flows = []
    for _ in range(5):
      _flows = create_random_flow(dead_ends, edges, number_of_busy_directions=1)
      for flow in _flows:
        flow.change_begin(begin)
      begin += duration
      flows += _flows
    sumo_rl.models.sumo.Routes([], [], [], flows).to_xml_file(cli_args.output_file)
  elif cli_args.all:
    os.system("rm -rf %s" % (cli_args.output_dir))
    all_flows = create_all_flows(dead_ends, edges, number_of_busy_directions=1)
    for idx, flows in enumerate(all_flows):
      directory = "%s-%s" % (cli_args.scenario, idx)
      os.makedirs("%s/%s" % (cli_args.output_dir, directory))
      os.system("cp ./skel/* %s/%s" % (cli_args.output, directory))
      os.system("cp %s %s/%s" % (network_file, cli_args.output_dir, directory))
      routes_file = "%s/%s/routes.rou.xml" % (cli_args.output_dir, directory)
      sumo_rl.models.sumo.Routes([], [], [], flows).to_xml_file(routes_file)
