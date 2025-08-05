from __future__ import annotations
import enum
import os
import argparse
import sys
import random
import abc
import typing
import copy
import re
from typing import Generator
import sumo_rl.models.flows
from sumo_rl.models.serde import GenericFile, SerdeDict, SerdeYaml, SerdeYamlFile
import sumo_rl.models.sumo
#random.seed(170701)
DEFAULT_TOTAL_DURATION = 100000
DEFAULT_SLOT_DURATION = 360

def shuffle(A: list) -> list:
  return sorted(A, key = lambda _ : random.random())

def random_binomial(p: float) -> bool:
  return random.random() <= p

def line_is_table_header(line: str):
  mo = re.match(r'^\|(\s+[^|]+\s+\|)+$', line)
  return mo is not None

def line_is_table_row(line: str):
  mo = re.match(r'^\|(\s+[^|]+\s+\|)+$', line)
  return mo is not None

def line_is_table_separator(line: str):
  mo = re.match(r'^\|(\s+[-]+\s+\|)+$', line)
  return mo is not None

def extract_table_field_names(line: str):
  mo = re.findall(r'\s+([^|]+)\s+\|', line)
  return [_.strip() for _ in mo]

def extract_table_fields(line: str):
  mo = re.findall(r'\s+([^|]+)\s+\|', line)
  return [_.strip() for _ in mo]

def read_all_tables_from_md_file(md_file: str) -> list[dict[str, list]]:
  tables: list[dict[str, list]] = []

  reading_table: bool = False
  with open(md_file, mode='r', encoding='utf-8') as file:
    for line_num, line in enumerate(file):
      line = line.strip()
      if not reading_table:
        if line_is_table_header(line):
          field_names = extract_table_field_names(line)
          tables.append({field_name:[] for field_name in field_names})
          reading_table = True
      else:
        if line_is_table_separator(line):
          pass
        elif line_is_table_row(line):
          fields = extract_table_fields(line)
          table_field_names = list(tables[-1].keys())
          number_of_fields_in_table = len(table_field_names)
          number_of_fields_in_row = len(fields)
          if number_of_fields_in_table != number_of_fields_in_row:
            raise ValueError('Current table expects %s fields but current row (%s) has %s fields' % (
              number_of_fields_in_table,
              line_num,
              number_of_fields_in_row
            ))
          for field_num, field_name in enumerate(table_field_names):
            tables[-1][field_name].append(fields[field_num])
        else:
          reading_table = False
  return tables

def iterrows(table: dict[str, list]) -> Generator[dict, None, None]:
  keys = list(table.keys())
  table_length = len(table[keys[0]])
  for row in range(table_length):
    yield {key: table[key][row] for key in keys}

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
    elif value.lower() == 'veryhigh':
      return TrafficLevel.VERY_HIGH.value
    elif value.lower() == 'ridiculous':
      return TrafficLevel.RIDICULOUS.value
    elif value.lower() == 'zero':
      return TrafficLevel.NO.value
    elif value.lower() == 'basso':
      return TrafficLevel.LOW.value
    elif value.lower() == 'medio':
      return TrafficLevel.MEDIUM.value
    elif value.lower() == 'alto':
      return TrafficLevel.HIGH.value
    elif value.lower() == 'molto alto':
      return TrafficLevel.VERY_HIGH.value
    elif value.lower() == 'ridicolo':
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
        if random_binomial(p=self.slot_probability) == 1:
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
                                  symmetric=(data.get('symmetric') == True),
                                  reversed=(data.get('reversed') == True),
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
                                  symmetric=(data.get('symmetric') == True),
                                  reversed=(data.get('reversed') == True),
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
    if random_binomial(p=self.slot_probability) == 1:
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, side_dead_ends)):
        self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_side)
      for (A, B) in filter(lambda P: P[0].id != P[1].id, comb(side_dead_ends, main_dead_ends)):
        self.add_traffic_to_design(design, A, B, self.traffic_levels.side_to_main)
    return design

  def create_sparse_design(self, network: sumo_rl.models.flows.Network):
    design: dict[tuple[str, str], float] = {}
    for axis in network.layout.main_axes:
      self.add_traffic_to_design(design, axis.A, axis.B, self.traffic_levels.main_to_main)
    if random_binomial(p=self.slot_probability) == 1:
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
                                    symmetric=(data.get('symmetric') == True),
                                    reversed=(data.get('reversed') == True),
                                    artificial_queue=(data.get('artificialQueue') == True))

class TransitionTrafficGenerator(TrafficGenerator):
  def __init__(self, phases: list[TrafficGenerator], total_duration: int, symmetric: bool = True, reversed: bool = False, artificial_queue: bool = False, title: str | None = None, description: str | None = None):
    N = len(phases)
    assert N >= 2
    if title is None:
      title = "-".join([phase.id for phase in phases])

    if description is None:
      description = "Transition " + "->".join([phase.quote_or_cite() for phase in phases])

    super().__init__(total_duration=total_duration, symmetric=symmetric, reversed=reversed, artificial_queue=artificial_queue, title=title, description=description)
    self.phases = []
    for phase in phases:
      phase = copy.deepcopy(phase)
      phase.change_duration(self.total_duration // N)
      phase.symmetric = symmetric
      phase.reversed = reversed
      phase.artificial_queue = artificial_queue
      self.phases.append(phase)

  def __call__(self, network: sumo_rl.models.flows.Network) -> list[sumo_rl.models.flows.Flow]:
    flows = sumo_rl.models.flows.Flows([])
    for phase in self.phases:
      flows.concat(phase(network))
    return flows.unpack()

  def to_dict(self) -> dict:
    return {
      'type': 'transition',
      'phases': [phase.to_dict() for phase in self.phases],
      'duration': self.total_duration,
      'title': self.title,
      'description': self.description
    }

  @staticmethod
  def from_dict(data: dict) -> TransitionTrafficGenerator:
    assert data['type'] == 'transition'
    return TransitionTrafficGenerator(phases=[traffic_generator_from_dict(phase) for phase in data['phases']],
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

  def gets(self, IDs: list[str]) -> list[TrafficGenerator]:
    return list(map(lambda ID: self.get(ID), IDs))

  def set(self, ID: str, traffic_generator: TrafficGenerator) -> TrafficGenerator:
    self.registry[ID] = traffic_generator
    return self.get(ID)

  def autoset(self, traffic_generator: TrafficGenerator) -> TrafficGenerator:
    ID = traffic_generator.id
    self.registry[ID] = traffic_generator
    return self.get(ID)

  def variants(self) -> list[str]:
    return list(self.registry.keys())

  def simple_variants(self) -> list[str]:
    return list(filter(lambda s: '-' not in s, self.variants()))

  @staticmethod
  def Default() -> TrafficRegistry:
    registry = TrafficRegistry()
    registry.autoset(CasualTrafficGenerator(traffic_level=TrafficLevel.LOW.value,
                                            total_duration=DEFAULT_TOTAL_DURATION,
                                            slot_duration=DEFAULT_SLOT_DURATION,
                                            title='A',
                                            description='Low casual traffic',
                                            artificial_queue=False))
    registry.autoset(StableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.HIGH.value,
                                                                             main_to_side=TrafficLevel.LOW.value,
                                                                             side_to_main=TrafficLevel.LOW.value,
                                                                             side_to_side=TrafficLevel.MEDIUM.value),
                                            total_duration=DEFAULT_TOTAL_DURATION,
                                            dense=True,
                                            title='B',
                                            description='Intense stable traffic',
                                            artificial_queue=False))
    registry.autoset(UnstableTrafficGenerator(traffic_levels=AxisTrafficMatrix(main_to_main=TrafficLevel.MEDIUM.value,
                                                                               main_to_side=TrafficLevel.LOW.value,
                                                                               side_to_main=TrafficLevel.LOW.value,
                                                                               side_to_side=TrafficLevel.LOW.value),
                                              total_duration=DEFAULT_TOTAL_DURATION,
                                              slot_duration=DEFAULT_SLOT_DURATION,
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
      if variant['type'] == 'transition':
        phases = []
        for phase in variant['phases']:
          if isinstance(phase, str) and phase in data:
            phase = data[phase]
          phases.append(phase)
        variant['phases'] = phases
      registry.set(key, traffic_generator_from_dict(variant))
    return registry

class TrafficTranslator:
  @staticmethod
  def is_traffic_level_matrix(prop: str) -> bool:
    return prop[0] == '<' and prop[-1] == '>'

  @staticmethod
  def is_time_sequence(prop: str) -> bool:
    return prop[0] == '>' and prop[-1] == '>'

  @staticmethod
  def extract_traffic_level_matrix(prop: str) -> AxisTrafficMatrix:
    mm, ms, sm, ss = list(map(traffic_level_from_string, prop[1:-1].split(',')))
    return AxisTrafficMatrix(mm, ms, sm, ss)

  @staticmethod
  def extract_time_sequence(prop: str) -> list:
    return prop[1:-1].split('>>')

  @staticmethod
  def translate_md_row(ID: str, desc: str, spec_string: str) -> dict:
    props = spec_string.strip().split()
    specs = {
        'title': ID,
        'description': desc,
        'dense': False,
        'symmetric': False,
        'reversed': False,
        'artificialQueue': True,
    }

    for prop in props:
      if prop == 'Casuale':
        specs['type'] = 'casual'
      elif prop == 'Stabile':
        specs['type'] = 'stable'
      elif prop == 'Instabile':
        specs['type'] = 'unstable'
      elif prop == 'Transizione':
        specs['type'] = 'transition'
      elif prop == 'Simmetrico':
        specs['symmetric'] = True
      elif prop == 'Asimmetrico':
        specs['symmetric'] = False
      elif prop == 'Denso':
        specs['dense'] = True
      elif prop == 'Assiale':
        specs['dense'] = False
      elif prop == 'Inverso':
        specs['reversed'] = True
      elif prop == 'Diretto':
        specs['reversed'] = False
      elif __class__.is_time_sequence(prop):
        specs['timeSequence'] = __class__.extract_time_sequence(prop)
      elif __class__.is_traffic_level_matrix(prop):
        specs['trafficLevels'] = __class__.extract_traffic_level_matrix(prop).to_dict()
      else:
        specs['trafficLevel'] = traffic_level_from_string(prop)


    duration = DEFAULT_TOTAL_DURATION
    slotTime = DEFAULT_SLOT_DURATION
    if specs['type'] == 'casual':
      return {
        'type': specs['type'],
        'trafficLevel': specs['trafficLevel'],
        'duration': duration,
        'slotTime': slotTime,
        'title': specs['title'],
        'description': specs['description'],
        'artificialQueue': specs['artificialQueue'],
        'symmetric': specs['symmetric'],
        'reversed': specs['reversed']
      }
    elif specs['type'] == 'stable':
      return {
        'type': specs['type'],
        'trafficLevels': specs['trafficLevels'],
        'duration': duration,
        'title': specs['title'],
        'description': specs['description'],
        'dense': specs['dense'],
        'symmetric': specs['symmetric'],
        'reversed': specs['reversed'],
        'artificial_queue': specs['artificialQueue']
      }
    elif specs['type'] == 'unstable':
      return {
        'type': specs['type'],
        'trafficLevels': specs['trafficLevels'],
        'duration': duration,
        'slotTime': slotTime,
        'title': specs['title'],
        'description': specs['description'],
        'dense': specs['dense'],
        'symmetric': specs['symmetric'],
        'reversed': specs['reversed'],
        'artificial_queue': specs['artificialQueue']
      }
    elif specs['type'] == 'transition':
      return {
        'type': specs['type'],
        'duration': duration,
        'title': specs['title'],
        'description': specs['description'],
        'phases': specs['timeSequence']
      }
    else:
      raise ValueError(specs, props)

  @staticmethod
  def from_md_file_to_yml_file(md_file: str, yml_file: str):
    tables = read_all_tables_from_md_file(md_file)
    yml_registry = {}
    for table in tables:
      if list(table.keys()) == ['ID', 'Descrizione', 'Inquadramento']:
        for row in iterrows(table):
          yml_registry[row['ID']] = __class__.translate_md_row(row['ID'], row['Descrizione'], row['Inquadramento'])
    GenericFile(yml_registry).to_yaml_file(yml_file)

def summarize_traffic_complexity(traffic: list[sumo_rl.models.flows.Flow]):
  complexity = 0.0
  begin, end = min([flow.begin for flow in traffic]), max([flow.end for flow in traffic])
  duration = end - begin
  for flow in traffic:
    complexity += ((flow.end - flow.begin) / duration) * flow.vehsPerHour
  return complexity

def generate_traffic(base_dir: str, traffic_generator: TrafficGenerator, number: int, output_dir: str, relative_output_dir: str) -> list[tuple[str, float]]:
  assert number > 0
  network = sumo_rl.models.flows.Network.Load(base_dir)

  os.system('mkdir -p %s' % output_dir)
  os.system('cp %s/network.net.xml %s/network.net.xml' % (base_dir, output_dir))
  results = []
  for _ in range(number):
    traffic = traffic_generator(network)
    routes = sumo_rl.models.sumo.Routes(junction_flows=traffic)
    output_file = '%s/routes.%s.rou.xml' % (output_dir, _)
    relative_output_file = '%s/routes.%s.rou.xml' % (relative_output_dir, _)
    routes.to_xml_file(output_file)
    results.append((relative_output_file, summarize_traffic_complexity(traffic)))
  #simulation = sumo_rl.models.sumo.Simulation(network, routes, None)
  #simulation.to_xml_file('%s/simulation.sumocfg' % (output_dir))
  return results

def get_or_leave_integer(splitted: list[str], default_value: int) -> tuple[list[str], int]:
  try:
    number = int(splitted[0])
    splitted = splitted[1:]
    return splitted, number
  except:
    return splitted, default_value

def parse_properties_from_request(registry: TrafficRegistry, string: str) -> tuple[int, int, list[TrafficGenerator], bool]:
  splitted = string.strip().split(',')
  splitted, number = get_or_leave_integer(splitted, 1)
  splitted, duration = get_or_leave_integer(splitted, DEFAULT_TOTAL_DURATION)
  artificial_queue = False
  phases = []
  for desc in splitted:
    if desc == '£':
      artificial_queue = True
    elif desc == '*':
      phases += registry.gets(registry.simple_variants())
    elif desc == '~':
      phases = shuffle(phases)
    else:
      phases += [registry.get(desc)]
  return number, duration, phases, artificial_queue

def main():
  argument_parser = argparse.ArgumentParser(description='flower')
  argument_parser.add_argument('-s', '--scenario', default='celoria', help='Input scenario')
  argument_parser.add_argument('-S', '--seed', default=None, type=int, help='Input seed')
  argument_parser.add_argument('-ir', '--import-registry', default=None, type=str, help='Import traffic registry from md description')
  argument_parser.add_argument('-r', '--traffic-registry', default=None, type=str, help='Resume traffic registry from yml file')
  argument_parser.add_argument('-lt', '--list-traffic', default=False, action='store_true', help='Lists registered traffic types')
  argument_parser.add_argument('-dr', '--dump-registry', default='/tmp/traffic-registry.yml', type=str, help='Dumps traffic registry to yml file')
  argument_parser.add_argument('-at', '--all-traffics', default=False, action='store_true', help='Produces all registered traffic types')
  argument_parser.add_argument('-o', '--output', default='/tmp', type=str, help='Output directory')
  argument_parser.add_argument('-V', '--verbose', default=False, action='store_true', help='Use verbose output')
  argument_parser.add_argument('traffic', default=None, type=str, nargs='*', help='Registered traffic types to generate as descriptor (comma separated with multeplicity and duration, example: \'17,12345,A,B,C\' or just \'A\'). With \'*\' you include all non transition types and with \'~\' you shuffle all the previously declared phase of the string.')
  cli_args = argument_parser.parse_args(sys.argv[1:])
  base_dir = "scenarios/%s" % cli_args.scenario

  if cli_args.seed is not None:
    random.seed(cli_args.seed)

  registry: TrafficRegistry
  if cli_args.import_registry is not None:
    TrafficTranslator.from_md_file_to_yml_file(cli_args.import_registry, cli_args.dump_registry)
    return

  if cli_args.traffic_registry is not None:
    registry = TrafficRegistry.from_yaml_file(cli_args.traffic_registry)
  else:
    registry = TrafficRegistry.Default()
  registry.to_yaml_file(cli_args.dump_registry)

  if cli_args.list_traffic:
    if cli_args.verbose:
      print("Traffic Registry:")
      for ID in registry.variants():
        traffic_generator = registry.get(ID)
        print(" - ID: %s" % traffic_generator.id)
        print("   Title: %s" % traffic_generator.title)
        print("   Description: %s" % traffic_generator.description)
    else:
      print("Traffic Registry:", registry.variants())
    return

  traffic_generators = []
  if cli_args.all_traffics:
    traffic_generators = list(map(lambda variant: (registry.get(variant), 1), registry.variants()))
  elif cli_args.traffic is not None:
    for traffic in cli_args.traffic:
      number, duration, phases, artificial_queue = parse_properties_from_request(registry, traffic)
      print(traffic)
      traffic_generators += [(TransitionTrafficGenerator(phases=phases, total_duration=duration, artificial_queue=artificial_queue), number)]

  results: list[sumo_rl.models.flows.Flow] = []
  for (traffic_generator, number) in traffic_generators:
    output = "%s/%s" % (cli_args.output, traffic_generator.id)
    relative_output = "%s" % (traffic_generator.id,)
    print("Producing %s / %s / %s" % (traffic_generator.id, traffic_generator.title, traffic_generator.description))
    results += generate_traffic(base_dir, traffic_generator, number, output, relative_output)
  results = sorted(results, key = lambda k: k[1])
  with open("%s/order.yml" % (cli_args.output,), mode='w', encoding='utf-8') as file:
    for result in results:
      file.write("- %s # %s\n" % (result[0], result[1]))

if __name__ == "__main__":
  main()
