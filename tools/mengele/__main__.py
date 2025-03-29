from __future__ import annotations
import enum
import os
import argparse
import sys
import random
import abc
import typing
import copy
from typing import Generator
import sumo_rl.models.flows
from sumo_rl.models.serde import SerdeDict, SerdeYaml, SerdeYamlFile
import sumo_rl.models.sumo
#random.seed(170701)

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

def traffic_level_from_string(value: str|float|int) -> float:
  try:
    return float(value)
  except:
    value = str(value)
    if value.lower() == 'no':
      return TrafficLevel.NO.value
    elif value.lower() == 'low':
      return TrafficLevel.LOW.value
    elif value.lower() == 'medium':
      return TrafficLevel.MEDIUM.value
    elif value.lower() == 'high':
      return TrafficLevel.HIGH.value
    elif value.lower() == 'veryHigh':
      return TrafficLevel.VERY_HIGH.value
    elif value.lower() == 'ridiculous':
      return TrafficLevel.RIDICULOUS.value
    else:
      raise ValueError('Expected a traffic level, got "%s"' % value)

class AxisTrafficMatrix(SerdeYaml):
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
  def from_dict(traffic_levels: dict) -> AxisTrafficMatrix:
    return AxisTrafficMatrix(main_to_main=float(traffic_level_from_string(str(traffic_levels['main->main']))),
                             main_to_side=float(traffic_level_from_string(str(traffic_levels['main->side']))),
                             side_to_main=float(traffic_level_from_string(str(traffic_levels['side->main']))),
                             side_to_side=float(traffic_level_from_string(str(traffic_levels['side->side']))))

  def to_dict(self) -> dict:
    return {
        'main->main': self.main_to_main,
        'main->side': self.main_to_side,
        'side->main': self.side_to_main,
        'side->side': self.side_to_side
      }

class TrafficGenerator(SerdeDict):
  INCREMENTAL_IDX = 0
  @staticmethod
  def nextID() -> str:
    id = TrafficGenerator.INCREMENTAL_IDX
    TrafficGenerator.INCREMENTAL_IDX += 1
    return 'TG' + str(id)

  def __init__(self, total_duration: int, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str|None = None, description: str|None = None):
    assert total_duration > 0
    self.total_duration: int  = total_duration
    self.symmetric = symmetric
    self.reversed = reversed
    self.artificial_queue = artificial_queue
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

  def change_duration(self, total_duration: int) -> None:
    self.total_duration = total_duration

  def add_traffic_to_design(self, design: dict[tuple[str, str], float], A: sumo_rl.models.flows.DeadEnd, B: sumo_rl.models.flows.DeadEnd, traffic_level: float):
    if (A.id, B.id) not in design:
      design[(A.id, B.id)] = traffic_level
    else:
      if traffic_level > design[(A.id, B.id)]:
        design[(A.id, B.id)] = traffic_level

  def render_design(self, design: dict[tuple[str, str], float], begin: int, end: int, capacities: dict[str, int]) -> list[sumo_rl.models.flows.Flow]:
    flows: list[sumo_rl.models.flows.Flow] = []
    arrivalSpeed = (0.0 if self.artificial_queue else None)
    for ((A_id, B_id), traffic_level) in design.items():
      if not self.symmetric:
        if self.reversed:
          if A_id < B_id and (B_id, A_id) in design:
            traffic_level /= 2
        else:
          if A_id > B_id and (B_id, A_id) in design:
            traffic_level /= 2
      capacity = capacities[A_id]
      vehq = capacity * traffic_level * random.random()
      flows.append(sumo_rl.models.flows.Flow(sumo_rl.models.flows.Flow.nextID(), begin, end, A_id, B_id, vehq, arrivalSpeed=arrivalSpeed))
    return flows

class SlottedTrafficGenerator(TrafficGenerator):
  def __init__(self, total_duration: int, slot_probability: float = 0.7, slots_number: int|None = None, slot_duration: int|None = None, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str|None = None, description: str|None = None):
    super().__init__(total_duration=total_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
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
    
    self.slot_probability = slot_probability
    self.total_duration = total_duration
    self.slots_number = slots_number
    self.slot_duration = slot_duration

  def change_duration(self, total_duration: int) -> None:
    self.total_duration = total_duration
    self.slots_number = self.total_duration // self.slot_duration

class CasualTrafficGenerator(SlottedTrafficGenerator):
  """
  Casual and slotted traffic generator.
  """
  def __init__(self, traffic_level: float, total_duration: int, slot_probability: float = 0.7, slots_number: int | None = None, slot_duration: int | None = None, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str|None = None, description: str|None = None):
    super().__init__(total_duration=total_duration, slot_probability=slot_probability, slots_number=slots_number, slot_duration=slot_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
    assert traffic_level > 0 and traffic_level <= 1
    self.traffic_level = traffic_level

  def creare_slot_design(self, network: sumo_rl.models.flows.Network) -> dict[tuple[str, str], float]:
    design: dict[tuple[str, str], float] = {}
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(network.dead_ends.values(), network.dead_ends.values())):
      if A.id != B.id:
        if random.binomialvariate(p=self.slot_probability) == 1:
          self.add_traffic_to_design(design, A, B, self.traffic_level)
    return design

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    capacities = network.flow_capacities

    flows: list[sumo_rl.models.flows.Flow] = []
    for slot in range(self.slots_number):
      begin, end = self.slot_duration * slot, self.slot_duration * (slot + 1)
      design = self.creare_slot_design(network)
      flows += self.render_design(design, begin, end, capacities)
    return flows

  def to_dict(self) -> dict:
    return {
      'type': 'casual',
      'trafficLevel': self.traffic_level,
      'duration': self.total_duration,
      'slotProbability': self.slot_probability,
      'slots': self.slots_number,
      'slotTime': self.slot_duration,
      'symmetric': self.symmetric,
      'reversed': self.reversed,
      'artificialQueue': self.artificial_queue,
      'title': self.title,
      'description': self.description
    }

  @staticmethod
  def from_dict(data: dict) -> CasualTrafficGenerator:
    assert data['type'] == 'casual'
    return CasualTrafficGenerator(traffic_level=traffic_level_from_string(data['trafficLevel']),
                                  total_duration=data['duration'],
                                  slot_duration=data['slotTime'],
                                  title=data['title'],
                                  description=data['description'],
                                  artificial_queue=(data.get('artificialQueue') == True))

class StableTrafficGenerator(TrafficGenerator):
  """
  Stable and axis-based traffic generator.
  """
  def __init__(self, traffic_levels: AxisTrafficMatrix, total_duration: int, dense: bool = True, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str|None = None, description: str|None = None):
    super().__init__(total_duration=total_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
    self.traffic_levels = traffic_levels
    self.dense = dense

  def create_dense_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}

    main_dead_ends = network.layout.main_dead_ends()
    side_dead_ends = network.layout.side_dead_ends()
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, main_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.main_to_main)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, side_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.main_to_side)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, side_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_side)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, main_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_main)
    return design

  def create_sparse_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    for axis in network.layout.main_axes:
      self.add_traffic_to_design(design, axis.A, axis.B, self.traffic_levels.main_to_main)
    for axis in network.layout.side_axes:
      self.add_traffic_to_design(design, axis.A, axis.B, self.traffic_levels.side_to_side)
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
    flows: list[sumo_rl.models.flows.Flow] = self.render_design(design, begin, end, capacities)
    return flows

  @staticmethod
  def from_dict(data: dict) -> StableTrafficGenerator:
    assert data['type'] == 'stable'
    return StableTrafficGenerator(traffic_levels=AxisTrafficMatrix.from_dict(data['trafficLevels']),
                                  total_duration=data['duration'],
                                  title=data['title'],
                                  description=data['description'],
                                  dense=(data.get('dense') == True),
                                  artificial_queue=(data.get('artificialQueue') == True))

  def to_dict(self) -> dict:
    return {
      'type': 'stable',
      'trafficLevels': self.traffic_levels.to_dict(),
      'duration': self.total_duration,
      'dense': self.dense,
      'symmetric': self.symmetric,
      'reversed': self.reversed,
      'artificialQueue': self.artificial_queue,
      'title': self.title,
      'description': self.description
    }

class UnstableTrafficGenerator(SlottedTrafficGenerator):
  """
  Unstable and slotted traffic generator.
  """
  def __init__(self, traffic_levels: AxisTrafficMatrix, total_duration: int, slot_probability: float = 0.7, slots_number: int|None = None, slot_duration: int|None = None, dense: bool = True, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str|None = None, description: str|None = None):
    super().__init__(total_duration=total_duration, slot_probability=slot_probability, slots_number=slots_number, slot_duration=slot_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
    self.traffic_levels = traffic_levels
    self.dense = dense

  def create_dense_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}

    main_dead_ends = network.layout.main_dead_ends()
    side_dead_ends = network.layout.side_dead_ends()
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, main_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.main_to_main)
    for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(main_dead_ends, side_dead_ends)):
      self.add_traffic_to_design(design, A, B, self.traffic_levels.main_to_side)
    if random.binomialvariate(p=self.slot_probability) == 1:
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, side_dead_ends)):
        self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_side)
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, main_dead_ends)):
        self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_main)
    return design

  def create_sparse_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    for axis in network.layout.main_axes:
      self.add_traffic_to_design(design, axis.A, axis.B, self.traffic_levels.main_to_main)
    if random.binomialvariate(p=self.slot_probability) == 1:
      for axis in network.layout.side_axes:
        self.add_traffic_to_design(design, axis.A, axis.B, self.traffic_levels.side_to_side)
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
      flows += self.render_design(design, begin, end, capacities)
    return flows

  def to_dict(self) -> dict:
    return {
      'type': 'unstable',
      'trafficLevels': self.traffic_levels.to_dict(),
      'duration': self.total_duration,
      'slotProbability': self.slot_probability,
      'slots': self.slots_number,
      'slotTime': self.slot_duration,
      'dense': self.dense,
      'symmetric': self.symmetric,
      'reversed': self.reversed,
      'artificialQueue': self.artificial_queue,
      'title': self.title,
      'description': self.description
    }

  @staticmethod
  def from_dict(data: dict) -> UnstableTrafficGenerator:
    assert data['type'] == 'unstable'
    return UnstableTrafficGenerator(traffic_levels=AxisTrafficMatrix.from_dict(data['trafficLevels']),
                                    total_duration=data['duration'],
                                    slot_duration=data['slotTime'],
                                    dense=(data.get('dense') == True),
                                    title=data['title'],
                                    description=data['description'],
                                    artificial_queue=(data.get('artificialQueue') == True))

class TransitionTrafficGenerator(TrafficGenerator):
  def __init__(self, initial: TrafficGenerator, ending: TrafficGenerator, total_duration: int, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str | None = None, description: str | None = None):
    if title is None:
      title = "%s-%s" % (initial.id, ending.id)

    if description is None:
      description = "Transition from %s to %s" % (initial.quote_or_cite(), ending.quote_or_cite())

    super().__init__(total_duration=total_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
    self.initial = copy.deepcopy(initial)
    self.ending = copy.deepcopy(ending)
    self.initial.change_duration(self.total_duration // 2)
    self.ending.change_duration(self.total_duration - self.initial.total_duration)
    self.initial.symmetric = symmetric
    self.initial.reversed = reversed
    self.initial.artificial_queue = artificial_queue
    self.ending.symmetric = symmetric
    self.ending.reversed = reversed
    self.ending.artificial_queue = artificial_queue

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    flows = sumo_rl.models.flows.Flows([])
    flows.concat(self.initial(network))
    flows.concat(self.ending(network))
    return flows.unpack()

  def to_dict(self) -> dict:
    return {
      'type': 'transition',
      'initial': self.initial.to_dict(),
      'ending': self.ending.to_dict(),
      'duration': self.total_duration,
      'title': self.title,
      'description': self.description
    }

  @staticmethod
  def from_dict(data: dict) -> TransitionTrafficGenerator:
    assert data['type'] == 'transition'
    return TransitionTrafficGenerator(initial=traffic_generator_from_dict(data['initial']),
                                      ending=traffic_generator_from_dict(data['ending']),
                                      total_duration=data['duration'],
                                      title=data['title'],
                                      description=data['description'])

def traffic_generator_from_dict(data: dict) -> TrafficGenerator:
  if data['type'] == 'casual':
    return CasualTrafficGenerator.from_dict(data)
  if data['type'] == 'stable':
    return StableTrafficGenerator.from_dict(data)
  if data['type'] == 'unstable':
    return UnstableTrafficGenerator.from_dict(data)
  if data['type'] == 'transition':
    return TransitionTrafficGenerator.from_dict(data)
  else:
    raise ValueError('Uknown traffic generator type "%s"' % data['type'])

class TrafficRegistry(SerdeYamlFile):
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
    default_total_duration: int = 10000
    default_slot_duration: int = 60

    registry = TrafficRegistry()
    registry.autoset(CasualTrafficGenerator(traffic_level=TrafficLevel.LOW.value,
                                            total_duration=default_total_duration,
                                            slot_duration=default_slot_duration,
                                            title='A',
                                            description='Low casual traffic',
                                            artificial_queue=False))
    registry.autoset(StableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.HIGH.value,
                                                                             main_to_side=TrafficLevel.LOW.value,
                                                                             side_to_main=TrafficLevel.LOW.value,
                                                                             side_to_side=TrafficLevel.MEDIUM.value),
                                            total_duration=default_total_duration,
                                            dense=True,
                                            title='B',
                                            description='Intense stable traffic',
                                            artificial_queue=False))
    registry.autoset(UnstableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.MEDIUM.value,
                                                                               main_to_side=TrafficLevel.LOW.value,
                                                                               side_to_main=TrafficLevel.LOW.value,
                                                                               side_to_side=TrafficLevel.LOW.value),
                                              total_duration=default_total_duration,
                                              slot_duration=default_slot_duration,
                                              dense=True,
                                              title='C',
                                              description='Intermediate traffic in main/side branches with frequent interruption from side branches',
                                              artificial_queue=False))
    return registry

  def to_dict(self) -> dict:
    return {key:variant.to_dict() for key, variant in self.registry.items()}

  @staticmethod
  def from_dict(data: dict) -> TrafficRegistry:
    registry = TrafficRegistry()
    for key, variant in data.items():
      registry.set(key, traffic_generator_from_dict(variant))
    return registry

def generate_traffic(base_dir: str, traffic_generator: TrafficGenerator, number: int, output_dir: str):
  assert number > 0
  network = sumo_rl.models.flows.Network.Load(base_dir)

  os.system('mkdir -p %s' % output_dir)
  os.system('cp %s/network.net.xml %s/network.net.xml' % (base_dir, output_dir))
  for _ in range(number):
    traffic = traffic_generator(network)
    routes = sumo_rl.models.sumo.Routes(junction_flows=traffic)
    routes.to_xml_file('%s/routes.%s.rou.xml' % (output_dir, _))
  simulation = sumo_rl.models.sumo.Simulation(network, routes, None)
  simulation.to_xml_file('%s/simulation.sumocfg' % (output_dir))

def main():
  argument_parser = argparse.ArgumentParser(description='flower')
  argument_parser.add_argument('-s', '--scenario', default='breda', help='Input scenario')
  argument_parser.add_argument('-r', '--traffic-registry', default=None, type=str, help='Resume traffic registry from yml file')
  argument_parser.add_argument('-t', '--traffic', default=None, type=str, help='Registered traffic type to generate')
  argument_parser.add_argument('-lt', '--list-traffic', default=False, action='store_true', help='Lists registered traffic types')
  argument_parser.add_argument('-dr', '--dump-registry', default='/tmp/traffic-registry.yml', type=str, help='Dumps traffic registry to yml file')
  argument_parser.add_argument('-at', '--all-traffics', default=False, action='store_true', help='Produces all registered traffic types')
  argument_parser.add_argument('-n', '--number', default=1, type=int, help='Number of routes files to generate')
  argument_parser.add_argument('-o', '--output', default='/tmp', type=str, help='Output directory')
  cli_args = argument_parser.parse_args(sys.argv[1:])
  base_dir = "scenarios/%s" % cli_args.scenario

  registry: TrafficRegistry
  if cli_args.traffic_registry is not None:
    registry = TrafficRegistry.from_yaml_file(cli_args.traffic_registry)
  else:
    registry = TrafficRegistry.Default()
  registry.to_yaml_file(cli_args.dump_registry)

  if cli_args.list_traffic:
    print("Traffic Registry:")
    for ID in registry.variants():
      traffic_generator = registry.get(ID)
      print(" - ID: %s" % traffic_generator.id)
      print("   Title: %s" % traffic_generator.title)
      print("   Description: %s" % traffic_generator.description)
    return

  if cli_args.all_traffics:
    for variant in registry.variants():
      output = "%s/%s" % (cli_args.output, variant)
      traffic_generator = registry.get(variant)
      print("Producing %s / %s / %s" % (traffic_generator.id, traffic_generator.title, traffic_generator.description))
      generate_traffic(base_dir, traffic_generator, cli_args.number, output)
  elif cli_args.traffic is not None:
    generate_traffic(base_dir, registry.get(cli_args.traffic), cli_args.number, cli_args.output)

if __name__ == "__main__":
  main()
