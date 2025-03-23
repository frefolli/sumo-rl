from __future__ import annotations
import enum
import os
import argparse
import sys
import random
import abc
import typing
from typing import Generator
import sumo_rl.models.flows
import sumo_rl.models.sumo
random.seed(170701)

def comb(A: list|set, B: list|set) -> Generator[tuple, None, None]:
  for a in A:
    for b in B:
      yield (a, b)

class TrafficLevel(enum.Enum):
  NO=0.0
  LOW=0.05
  MEDIUM=0.2
  HIGH=0.5
  VERY_HIGH=0.8
  RIDICULOUS=1.0

class AxisTrafficMatrix:
  def __init__(self, main_to_main: float, main_to_side: float, side_to_main: float, side_to_side: float) -> None:
    self.main_to_main: float = main_to_main
    self.main_to_side: float = main_to_side
    self.side_to_main: float = side_to_main
    self.side_to_side: float = side_to_side

  @staticmethod
  def by_source(from_main: float, from_side: float) -> AxisTrafficMatrix:
    return AxisTrafficMatrix(
        main_to_main=from_main,
        main_to_side=from_main,
        side_to_main=from_side,
        side_to_side=from_side,
        )

  @staticmethod
  def by_target(to_main: float, to_side: float) -> AxisTrafficMatrix:
    return AxisTrafficMatrix(
        main_to_main=to_main,
        main_to_side=to_side,
        side_to_main=to_main,
        side_to_side=to_side,
        )

  @staticmethod
  def from_dict(traffic_levels: dict[tuple[str, str], float]) -> AxisTrafficMatrix:
    return AxisTrafficMatrix(main_to_main = float(traffic_levels[('main', 'main')]),
                             main_to_side = float(traffic_levels[('main', 'side')]),
                             side_to_main = float(traffic_levels[('side', 'main')]),
                             side_to_side = float(traffic_levels[('side', 'side')]))

  def to_dict(self) -> dict[tuple[str, str], float]:
    return {
        ('main', 'main'): self.main_to_main,
        ('main', 'side'): self.main_to_side,
        ('side', 'main'): self.side_to_main,
        ('side', 'side'): self.side_to_side
        }

class TrafficGenerator(abc.ABC):
  INCREMENTAL_IDX = 0
  @staticmethod
  def nextID() -> str:
    id = TrafficGenerator.INCREMENTAL_IDX
    TrafficGenerator.INCREMENTAL_IDX += 1
    return 'TG' + str(id)

  def __init__(self, title: str|None = None, description: str|None = None):
    self.title: str|None = title
    self.description: str|None = description
    if self.title is not None:
      self.id = self.title
    else:
      self.id = self.nextID()

  def quote_or_cite(self) -> str:
    if self.description is None:
      return "\"%s\"-type traffic" % self.id
    else:
      return "<<%s>>" % self.description

  @abc.abstractmethod
  def __call__(self, network: sumo_rl.models.flows.Network, *args: typing.Any, **kwds: typing.Any) -> list[sumo_rl.models.flows.Flow]:
    """
    Processes the Network producing traffic according to constructor configuration and eventual other parameters passed to __call__
    """
    pass

class SlottedTrafficGenerator(TrafficGenerator):
  def __init__(self, total_duration: int, slot_probability: float = 0.7, slots_number: int|None = None, slot_duration: int|None = None, title: str|None = None, description: str|None = None):
    super().__init__(title, description)
    assert total_duration > 0
    if slots_number is None and slot_duration is None:
      slots_number = 1
      slot_duration = total_duration
    if slots_number is None:
      assert slot_duration > 0
      slots_number = total_duration // slot_duration
      assert slots_number > 0
    if slot_duration is None:
      assert slots_number > 0
      slot_duration = total_duration // slots_number
      assert slot_duration > 0
    assert slot_probability > 0 and slot_probability <= 1
    
    self.total_duration = total_duration
    self.slot_probability = slot_probability
    self.total_duration = total_duration
    self.slots_number = slots_number
    self.slot_duration = slot_duration

class CasualTrafficGenerator(SlottedTrafficGenerator):
  """
  Casual and slotted traffic generator.
  """
  def __init__(self, traffic_level: float, total_duration: int, slot_probability: float = 0.7, slots_number: int | None = None, slot_duration: int | None = None, title: str|None = None, description: str|None = None):
    super().__init__(total_duration, slot_probability, slots_number, slot_duration, title, description)
    assert traffic_level > 0 and traffic_level <= 1
    self.traffic_level = traffic_level

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    capacities = network.flow_capacities

    flows: list[sumo_rl.models.flows.Flow] = []
    for slot in range(self.slots_number):
      begin, end = self.slot_duration * slot, self.slot_duration * (slot + 1)
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(network.dead_ends.values(), network.dead_ends.values())):
        if A.id != B.id:
          if random.binomialvariate(p=self.slot_probability) == 1:
            capacity = capacities[A.id]
            vehq = capacity * self.traffic_level * random.random()
            flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), begin, end, A.id, B.id, vehq))
    return flows

class StableTrafficGenerator(TrafficGenerator):
  """
  Stable and axis-based traffic generator.
  """
  def __init__(self, traffic_levels: AxisTrafficMatrix, total_duration: int, dense: bool = True, title: str|None = None, description: str|None = None):
    super().__init__(title, description)
    self.traffic_levels = traffic_levels
    self.total_duration = total_duration
    self.dense = dense

  def create_dense_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    def update_with_most_busy(A: sumo_rl.models.flows.DeadEnd, B: sumo_rl.models.flows.DeadEnd, traffic_level: float):
      if (A.id, B.id) not in design:
        design[(A.id, B.id)] = traffic_level
      else:
        if traffic_level > design[(A.id, B.id)]:
          design[(A.id, B.id)] = traffic_level

    main_dead_ends = network.layout.main_dead_ends()
    side_dead_ends = network.layout.side_dead_ends()
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, main_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.main_to_main)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, side_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.main_to_side)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, side_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.side_to_side)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, main_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.side_to_main)
    return design

  def create_sparse_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    for axis in network.layout.main_axes:
      design[(axis.A.id, axis.B.id)] = self.traffic_levels.main_to_main
    for axis in network.layout.side_axes:
      design[(axis.A.id, axis.B.id)] = self.traffic_levels.side_to_side
    return design

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    """
    If `dense` is True then:
      flows are added for each couple of dead ends depending on traffic levels
    else:
      flows are added strictly based on axis configuration (only bidirectional flows for pairs declared as axes are created)
    """
    begin, end = 0, self.total_duration

    design: dict[tuple[str, str], float]
    if self.dense:
      design = self.create_dense_design(network)
    else:
      design = self.create_sparse_design(network)

    capacities = network.flow_capacities
    flows: list[sumo_rl.models.flows.Flow] = []
    for ((A_id, B_id), traffic_level) in design.items():
      capacity = capacities[A_id]
      vehq = capacity * traffic_level * random.random()
      flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), begin, end, A_id, B_id, vehq))
    return flows

class UnstableTrafficGenerator(SlottedTrafficGenerator):
  """
  Unstable and slotted traffic generator.
  """
  def __init__(self, traffic_levels: AxisTrafficMatrix, total_duration: int, slot_probability: float = 0.7, slots_number: int|None = None, slot_duration: int|None = None, dense: bool = True, title: str|None = None, description: str|None = None):
    super().__init__(total_duration, slot_probability, slots_number, slot_duration, title, description)
    self.traffic_levels = traffic_levels
    self.dense = dense

  def create_dense_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    def update_with_most_busy(A: sumo_rl.models.flows.DeadEnd, B: sumo_rl.models.flows.DeadEnd, traffic_level: float):
      if (A.id, B.id) not in design:
        design[(A.id, B.id)] = traffic_level
      else:
        if traffic_level > design[(A.id, B.id)]:
          design[(A.id, B.id)] = traffic_level

    main_dead_ends = network.layout.main_dead_ends()
    side_dead_ends = network.layout.side_dead_ends()
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, main_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.main_to_main)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, side_dead_ends)):
      update_with_most_busy(A, B, self.traffic_levels.main_to_side)
    if random.binomialvariate(p=self.slot_probability) == 1:
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, side_dead_ends)):
        update_with_most_busy(A, B, self.traffic_levels.side_to_side)
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, main_dead_ends)):
        update_with_most_busy(A, B, self.traffic_levels.side_to_main)
    return design

  def create_sparse_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    for axis in network.layout.main_axes:
      design[(axis.A.id, axis.B.id)] = self.traffic_levels.main_to_main
    if random.binomialvariate(p=self.slot_probability) == 1:
      for axis in network.layout.side_axes:
        design[(axis.A.id, axis.B.id)] = self.traffic_levels.side_to_side
    return design

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    flows: list[sumo_rl.models.flows.Flow] = []
    capacities = network.flow_capacities
    for slot in range(self.slots_number):
      begin, end = self.slot_duration * slot, self.slot_duration * (slot + 1)
      design: dict[tuple[str, str], float]
      if self.dense:
        design = self.create_dense_design(network)
      else:
        design = self.create_sparse_design(network)

      for ((A_id, B_id), traffic_level) in design.items():
        capacity = capacities[A_id]
        vehq = capacity * traffic_level * random.random()
        flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), begin, end, A_id, B_id, vehq))
    return flows

class TransitionTrafficGenerator(TrafficGenerator):
  def __init__(self, initial: TrafficGenerator, ending: TrafficGenerator, title: str | None = None, description: str | None = None):
    if title is None:
      title = "%s-%s" % (initial.id, ending.id)

    if description is None:
      description = "Transition from %s to %s" % (initial.quote_or_cite(), ending.quote_or_cite())

    super().__init__(title, description)
    self.initial = initial
    self.ending = ending

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    flows = sumo_rl.models.flows.Flows([])
    flows.concat(self.initial(network))
    flows.concat(self.ending(network))
    return flows.unpack()

class TrafficRegistry:
  def __init__(self) -> None:
    self.registry: dict[str, TrafficGenerator] = {}

  def get(self, ID: str) -> TrafficGenerator:
    return self.registry[ID]

  def set(self, ID: str, traffic_generator: TrafficGenerator) -> TrafficGenerator:
    self.registry[ID] = traffic_generator
    return self.get(ID)

  def autoset(self, traffic_generator: TrafficGenerator) -> TrafficGenerator:
    ID = traffic_generator.id
    self.registry[ID] = traffic_generator
    return self.get(ID)

  def variants(self) -> list[str]:
    return list(self.registry.keys())
  
  def default(self) -> str:
    return self.variants()[0]

  @staticmethod
  def Default() -> TrafficRegistry:
    default_total_duration: int = 3600
    default_slot_duration: int = 60

    registry = TrafficRegistry()
    registry.autoset(CasualTrafficGenerator(traffic_level=TrafficLevel.LOW.value,
                                            total_duration=default_total_duration,
                                            slot_duration=default_slot_duration,
                                            title='A',
                                            description='Low casual traffic'))
    registry.autoset(StableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.HIGH.value,
                                                                             main_to_side=TrafficLevel.LOW.value,
                                                                             side_to_main=TrafficLevel.LOW.value,
                                                                             side_to_side=TrafficLevel.MEDIUM.value),
                                            total_duration=default_total_duration,
                                            dense=True,
                                            title='B',
                                            description='Intense stable traffic'))
    registry.autoset(UnstableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.MEDIUM.value,
                                                                               main_to_side=TrafficLevel.LOW.value,
                                                                               side_to_main=TrafficLevel.LOW.value,
                                                                               side_to_side=TrafficLevel.LOW.value),
                                              total_duration=default_total_duration,
                                              slot_duration=default_slot_duration,
                                              dense=True,
                                              title='C',
                                              description='Intermediate traffic in main/side branches with frequent interruption from side branches'))
    registry.autoset(TransitionTrafficGenerator(initial=registry.get('C'),
                                                ending=registry.get('B')))
    registry.autoset(TransitionTrafficGenerator(initial=registry.get('B'),
                                                ending=registry.get('C')))
    return registry

def generate_traffic(base_dir: str, network: sumo_rl.models.sumo.Network, traffic_generator: TrafficGenerator):
  traffic = traffic_generator(network)
  routes = sumo_rl.models.sumo.Routes(junction_flows=traffic)
  os.system('cp %s/network.net.xml /tmp/network.net.xml' % base_dir)
  routes.to_xml_file('/tmp/routes.rou.xml')
  simulation = sumo_rl.models.sumo.Simulation(network, routes, None)
  simulation.to_xml_file('/tmp/simulation.sumocfg')

def main():
  registry = TrafficRegistry.Default()

  argument_parser = argparse.ArgumentParser(description='flower')
  argument_parser.add_argument('-s', '--scenario', default='breda', help='Input scenario')
  argument_parser.add_argument('-t', '--traffic', default=registry.default(), choices=registry.variants(), help='Registered traffic type to generate')
  argument_parser.add_argument('-lt', '--list-traffic', default=False, action='store_true', help='list registered traffic types')
  cli_args = argument_parser.parse_args(sys.argv[1:])
  base_dir = "scenarios/%s" % cli_args.scenario

  if cli_args.list_traffic:
    print("Traffic Registry:")
    for ID in registry.variants():
      traffic_generator = registry.get(ID)
      print(" - ID: %s" % traffic_generator.id)
      print("   Title: %s" % traffic_generator.title)
      print("   Description: %s" % traffic_generator.description)
    return

  network = sumo_rl.models.flows.Network.Load(base_dir)
  generate_traffic(base_dir, network, registry.get(cli_args.traffic))

if __name__ == "__main__":
  main()
