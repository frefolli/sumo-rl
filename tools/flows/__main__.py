"""
Sogno tecnologico bolscevico
Atea mistica meccanica
Macchina automatica. No anima
"""

import sumo_rl.models.sumo
import sumo_rl.models.flows
import sumo_rl.models.commons
import matplotlib.pyplot
import argparse
import sys
import random
import os

random.seed(170701)

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
      flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), 0, duration, direction[0][0].id, direction[0][1].id, share * traffic_cap))
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

def execute_flow_design(dead_end_edges_map: dict[str, list[sumo_rl.models.flows.Edge]],
                        high_traffic_directions: list[tuple[sumo_rl.models.flows.DeadEnd, sumo_rl.models.flows.DeadEnd]],
                        low_traffic_directions: list[tuple[sumo_rl.models.flows.DeadEnd, sumo_rl.models.flows.DeadEnd]],
                        duration: int):
  traffic_caps = {
      de_id: sum([
        de_edge.flow_capacity
        for de_edge in de_edges
        ])
      for (de_id, de_edges) in dead_end_edges_map.items()
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
    high_traffic_directions, low_traffic_directions = sumo_rl.models.commons.extract_at_random(directions, number_of_busy_directions)
  flows = execute_flow_design(dead_end_edges_map, high_traffic_directions, low_traffic_directions, duration)
  return flows

def create_all_flows(dead_ends: list[sumo_rl.models.flows.DeadEnd],
                     edges: list[sumo_rl.models.flows.Edge],
                     duration: int,
                     number_of_busy_directions: int = None,
                     high_traffic_ratio: float = None) -> list[sumo_rl.models.flows.Flow]:
  directions, number_of_busy_directions, dead_end_edges_map = prepare_data_for_flow_design(dead_ends, edges, number_of_busy_directions, high_traffic_ratio)

  flows = []
  for (high_traffic_directions, low_traffic_directions) in sumo_rl.models.commons.extract_all_combs(directions, number_of_busy_directions):
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
  argument_parser.add_argument('-oD', '--output-dir', default='/tmp', help='Output directory')
  argument_parser.add_argument('-R', '--random', type=int, default=None, help='Generates an amount of random routes files')
  argument_parser.add_argument('-C', '--complex', type=int, default=None, help='Generates an amount of random complex routes files')
  argument_parser.add_argument('-b', '--busyness', type=int, default=1, help='How much busy directions there should be in a routes file')
  argument_parser.add_argument('-d', '--duration', type=int, default=10000, help='How much a flow configuration should be hold to last')
  argument_parser.add_argument('-c', '--complexity', type=int, default=5, help='How much flow configurations should be created in a complex routes file')
  argument_parser.add_argument('-A', '--all', action='store_true', help='Generates all routes files for atomic scenarious saving them as scenarios')
  argument_parser.add_argument('-o', '--overwrite', action='store_true', help='Don\'t remove output dir/file before writing')
  cli_args = argument_parser.parse_args(sys.argv[1:])

  base_dir = "scenarios/%s" % cli_args.scenario
  network_file = "%s/network.net.xml" % base_dir
  network = sumo_rl.models.flows.Network.Load(base_dir)

  if cli_args.random:
    if not cli_args.overwrite:
      os.system("rm -rf %s" % (cli_args.output_dir))
    sumo_rl.models.commons.ensure_dir(cli_args.output_dir)
    for idx in range(cli_args.random):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      flows = create_random_flow(list(network.dead_ends.values()), network.edges, duration=cli_args.duration//2, number_of_busy_directions=cli_args.busyness)
      routes = sumo_rl.models.sumo.Routes([], [], [], flows)
      routes.to_xml_file(path)
      plot_routes(routes, network.edges, path.replace('.xml', '.png'))
  elif cli_args.complex:
    if not cli_args.overwrite:
      os.system("rm -rf %s" % (cli_args.output_dir))
    sumo_rl.models.commons.ensure_dir(cli_args.output_dir)
    for idx in range(cli_args.complex):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      begin = 0
      flows = []
      for _ in range(cli_args.complexity):
        _flows = create_random_flow(list(network.dead_ends.values()), network.edges, duration=cli_args.duration, number_of_busy_directions=cli_args.busyness)
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
    all_flows = create_all_flows(list(network.dead_ends.values()), network.edges, duration=cli_args.duration, number_of_busy_directions=cli_args.busyness)
    for idx, flows in enumerate(all_flows):
      path = os.path.join(cli_args.output_dir, 'routes.%s.rou.xml' % idx)
      routes = sumo_rl.models.sumo.Routes([], [], [], flows)
      routes.to_xml_file(path)

if __name__ == "__main__":
  main()
