#!/usr/bin/env python3
import sumo_rl.models.sumo
import sumo_rl.models.topology
import sumo_rl.models.realization
from sumo_rl.models.commons import Point
import argparse
import sys
import random
random.seed(170701)

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

def cross_topology():
  topology = sumo_rl.models.topology.Topology()
  A = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(0, 0)))
  B = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(100, 0)))
  C = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(200, 0)))
  D = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(100, 100)))
  E = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(100, -100)))
  topology.double_link(A, B, 2)
  topology.double_link(B, C, 2)
  topology.double_link(D, B, 2)
  topology.double_link(E, B, 2)
  return topology

def t_way_topology():
  topology = sumo_rl.models.topology.Topology()
  A = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(0, 0)))
  B = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(0, 100)))
  C = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(100, 100)))
  D = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(-100, 100)))
  topology.double_link(A, B, 2)
  topology.double_link(B, C, 2)
  topology.double_link(B, D, 2)
  return topology

def line_topology():
  topology = sumo_rl.models.topology.Topology()
  A = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(0, 0)))
  for _ in range(5):
    B = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + 000, A.point.y + 100)))
    C = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + 100, A.point.y + 000)))
    D = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + 000, A.point.y - 100)))
    topology.double_link(A, B, 2)
    topology.double_link(A, C, 2)
    topology.double_link(A, D, 2)

    if _ == 0:
      E = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x - 100, A.point.y + 000)))
      topology.double_link(A, E, 2)
    A = C
  return topology

def generate_simple_linear(X: int, Y: int, Z: int) -> sumo_rl.models.topology.Topology:
  number_of_junctions_generator = lambda: random.randint(X // 2, 2 * X)
  edge_length_generator = lambda: random.randint(Y // 2, 2 * Y)
  ## Branches
  lane_number_generator = lambda: random.randint(1, Z)
  ## Main line
  lane_number = Z

  topology = sumo_rl.models.topology.Topology()
  A = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(0, 0)))
  for _ in range(number_of_junctions_generator()):
    B = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + 000, A.point.y + edge_length_generator())))
    C = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + edge_length_generator(), A.point.y + 000)))
    D = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x + 000, A.point.y - edge_length_generator())))
    K = lane_number_generator()
    topology.double_link(A, B, K)
    topology.double_link(A, C, lane_number)
    topology.double_link(A, D, K)
    if _ == 0:
      E = topology.add_node(sumo_rl.models.topology.Node(topology.next_node_ID(), Point(A.point.x - 100, A.point.y + 000)))
      topology.double_link(A, E, lane_number)
    A = C
  return topology

def generate_simple_rad() -> sumo_rl.models.topology.Topology:
  pass

if __name__ == "__main__":
  argument_parser = argparse.ArgumentParser(description="Generator of topologies for SUMO")
  argument_parser.add_argument('-it', '--input-topology', help='path to a topology file (*.top.json)')
  argument_parser.add_argument('-on', '--output-network', default="/tmp/network.net.xml", help='path to a SUMO network file that will be emitted (*.net.xml)')
  command_line_arguments = argument_parser.parse_args(sys.argv[1:])

  topology: sumo_rl.models.topology.Topology
  if command_line_arguments.input_topology:
    topology = sumo_rl.models.topology.Topology.from_json_file(command_line_arguments.input_topology)
  else:
    topology = generate_simple_linear(7, 100, 2)
  network = sumo_rl.models.realization.realize_topology(topology)
  network.to_xml_file("/tmp/network.net.xml")
