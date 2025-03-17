"""
Sogno tecnologico bolscevico
Atea mistica meccanica
Macchina automatica. No anima
"""

from typing import Generator
import xml.etree.ElementTree as ET
import sumo_rl.models.sumo
import sumo_rl.models.flows
import sumo_rl.models.commons
import matplotlib.pyplot
import argparse
import sys
import random
import os

random.seed(170701)

def is_reverse_of(A_id: str, B_id: str) -> bool:
  if A_id == '-' + B_id:
    return True
  if '-' + A_id == B_id:
    return True
  return False

def acquire_dead_ends(xml_root) -> list[sumo_rl.models.flows.DeadEnd]:
  dead_ends = []
  for child in xml_root:
    if child.tag == 'junction':
      if child.attrib['type'] == 'dead_end':
        dead_ends.append(sumo_rl.models.flows.DeadEnd(child.attrib['id']))
  return dead_ends

def parse_shape(shape_str: str) -> list[sumo_rl.models.commons.Point]:
  points_str = shape_str.split()
  shape: list[sumo_rl.models.commons.Point] = []
  for point_str in points_str:
    x_str, y_str = point_str.split(',')
    shape.append(sumo_rl.models.commons.Point(float(x_str), float(y_str)))
  return shape

def acquire_edges(xml_root) -> list[sumo_rl.models.flows.Edge]:
  edges = []
  for child in xml_root:
    if child.tag == 'edge':
      if 'function' not in child.attrib:
        edges.append(sumo_rl.models.flows.Edge(child.attrib['id'], child.attrib['from'], child.attrib['to'], [
          sumo_rl.models.flows.Lane(float(lane.attrib['length']), float(lane.attrib['speed']))
          for lane in child
          if ('allow' not in lane.attrib or lane.attrib['allow'] in ['all'])
        ], parse_shape(child.attrib['shape'])))
  return edges

def compute_flow_capacity_in_vehicles_per_hour(dead_ends: list[sumo_rl.models.flows.DeadEnd], edges: list[sumo_rl.models.flows.Edge]) -> int:
  dead_end_map = {dead_end.id:dead_end for dead_end in dead_ends}
  return sum([
    lane.flow_capacity()
    for edge in edges
    for lane in edge.lanes
    if (edge.from_junction in dead_end_map or edge.to_junction in dead_end_map)
  ])

def compute_queue_capacity_in_vehicles_per_hour(edges: list[sumo_rl.models.flows.Edge]) -> int:
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

def assign_flows(traffic_caps: dict[str, int],
                 headings: dict[str, list[tuple[tuple[sumo_rl.models.flows.DeadEnd, sumo_rl.models.flows.DeadEnd], bool]]],
                 duration: int):
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
      flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), 0, duration, direction[0][0], direction[0][1], share * traffic_cap))
  return flows

def prepare_data_for_flow_design(dead_ends: list[sumo_rl.models.flows.DeadEnd],
                                 edges: list[sumo_rl.models.flows.Edge],
                                 number_of_busy_directions: int = None,
                                 high_traffic_ratio: float = None):
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

def execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions, duration: int):
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

  return assign_flows(traffic_caps, headings, duration)

def create_random_flow(dead_ends: list[sumo_rl.models.flows.DeadEnd],
                       edges: list[sumo_rl.models.flows.Edge],
                       duration: int,
                       number_of_busy_directions: int = None,
                       high_traffic_ratio: float = None) -> list[sumo_rl.models.flows.Flow]:
  directions, number_of_busy_directions, dead_end_edges_map = prepare_data_for_flow_design(dead_ends, edges, number_of_busy_directions, high_traffic_ratio)

  high_traffic_directions: list[tuple[sumo_rl.models.flows.DeadEnd, sumo_rl.models.flows.DeadEnd]]
  low_traffic_directions: list[tuple[sumo_rl.models.flows.DeadEnd, sumo_rl.models.flows.DeadEnd]]
  if number_of_busy_directions == 0:
    high_traffic_directions = []
    low_traffic_directions = directions
  elif number_of_busy_directions == len(directions):
    high_traffic_directions = directions
    low_traffic_directions = []
  else:
    high_traffic_directions, low_traffic_directions = extract_at_random(directions, number_of_busy_directions)
  flows = execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions, duration)
  return flows

def create_all_flows(dead_ends: list[sumo_rl.models.flows.DeadEnd],
                     edges: list[sumo_rl.models.flows.Edge],
                     duration: int,
                     number_of_busy_directions: int = None,
                     high_traffic_ratio: float = None) -> list[sumo_rl.models.flows.Flow]:
  directions, number_of_busy_directions, dead_end_edges_map = prepare_data_for_flow_design(dead_ends, edges, number_of_busy_directions, high_traffic_ratio)

  flows = []
  for (high_traffic_directions, low_traffic_directions) in extract_all_combs(directions, number_of_busy_directions):
    flows.append(execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions, duration))
  return flows

def plot_routes(routes: sumo_rl.models.sumo.Routes, edges: list[sumo_rl.models.flows.Edge], png_path: str):
  junction_positions: dict[str, sumo_rl.models.commons.Point] = {}
  for edge in edges:
    junction_positions[edge.from_junction] = edge.shape[0]
    junction_positions[edge.to_junction] = edge.shape[-1]
  print(junction_positions)

  fig = matplotlib.pyplot.figure(figsize=(20,20))
  for junction_id, pos in junction_positions.items():
    matplotlib.pyplot.plot(pos.x, pos.y, marker='o', label=junction_id)

  for flow in routes.junction_flows:
    xi,yi = junction_positions[flow.fromJunction.id].as_tuple()
    xf, yf = junction_positions[flow.toJunction.id].as_tuple()
    dx, dy = xf - xi, yf - yi
    matplotlib.pyplot.annotate("", xytext=(xi, yi), xy=(xf, yf), arrowprops=dict(arrowstyle="->"))
  matplotlib.pyplot.legend()
  matplotlib.pyplot.savefig(png_path)
  matplotlib.pyplot.close()

def main():
  argument_parser = argparse.ArgumentParser(description='flower')
  argument_parser.add_argument('-s', '--scenario', default='lisca', help='Input scenario')
  argument_parser.add_argument('-oF', '--output-file', default='/tmp/routes.rou.xml', help='Output file')
  argument_parser.add_argument('-oD', '--output-dir', default='output', help='Output directory')
  argument_parser.add_argument('-R', '--random', type=int, default=None, help='Generates an amount of random routes files')
  argument_parser.add_argument('-C', '--complex', type=int, default=None, help='Generates an amount of random complex routes files')
  argument_parser.add_argument('-b', '--busyness', type=int, default=1, help='How much busy directions there should be in a routes file')
  argument_parser.add_argument('-d', '--duration', type=int, default=10000, help='How much a flow configuration should be hold to last')
  argument_parser.add_argument('-c', '--complexity', type=int, default=5, help='How much flow configurations should be created in a complex routes file')
  argument_parser.add_argument('-A', '--all', action='store_true', help='Generates all routes files for atomic scenarious saving them as scenarios')
  argument_parser.add_argument('-o', '--overwrite', action='store_true', help='Don\'t remove output dir/file before writing')
  cli_args = argument_parser.parse_args(sys.argv[1:])

  network_file = "scenarios/%s/network.net.xml" % cli_args.scenario
  tree = ET.parse(network_file)
  xml_root = tree.getroot()

  edges = acquire_edges(xml_root)
  dead_ends = acquire_dead_ends(xml_root)

  if cli_args.random:
    if not cli_args.overwrite:
      os.system("rm -rf %s" % (cli_args.output_dir))
    sumo_rl.models.commons.ensure_dir(cli_args.output_dir)
    for idx in range(cli_args.random):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      flows = create_random_flow(dead_ends, edges, duration=cli_args.duration//2, number_of_busy_directions=cli_args.busyness)
      routes = sumo_rl.models.sumo.Routes([], [], [], flows)
      routes.to_xml_file(path)
      plot_routes(routes, edges, path.replace('.xml', '.png'))
  elif cli_args.complex:
    if not cli_args.overwrite:
      os.system("rm -rf %s" % (cli_args.output_dir))
    sumo_rl.models.commons.ensure_dir(cli_args.output_dir)
    for idx in range(cli_args.complex):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      begin = 0
      flows = []
      for _ in range(cli_args.complexity):
        _flows = create_random_flow(dead_ends, edges, duration=cli_args.duration//2, number_of_busy_directions=cli_args.busyness)
        for flow in _flows:
          flow.change_begin(begin)
        begin += cli_args.duration
        flows += _flows
      routes = sumo_rl.models.sumo.Routes([], [], [], flows)
      routes.to_xml_file(path)
  elif cli_args.all:
    if not cli_args.overwrite:
      os.system("rm -rf %s" % (cli_args.output_dir))
    sumo_rl.models.commons.ensure_dir(cli_args.output_dir)
    all_flows = create_all_flows(dead_ends, edges, duration=cli_args.duration//2, number_of_busy_directions=cli_args.busyness)
    for idx, flows in enumerate(all_flows):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      routes = sumo_rl.models.sumo.Routes([], [], [], flows)
      routes.to_xml_file(path)

if __name__ == "__main__":
  main()
