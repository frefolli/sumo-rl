from __future__ import annotations
import math
import typing
import pickle
import time
import os
import os.path
import random
from typing import Generator

class Point:
  def __init__(self, x: float, y: float) -> None:
    self.x: float = x
    self.y: float = y

  def distance(self, o: Point) -> float:
    return math.sqrt(math.pow(self.x - o.x, 2) + math.pow(self.y - o.y, 2))

  def direction(self, o: Point) -> float:
    return math.atan2(self.y - o.y, self.x - o.x)

  def to_dict(self) -> dict:
    return {'x': self.x, 'y': self.y}

  def to_str(self) -> str:
    return "%s,%s" % (self.x, self.y)

  def to_xml(self) -> str:
    return "%s,%s" % (self.x, self.y)

  def as_tuple(self) -> tuple[float, float]:
    return (self.x, self.y)

  def __repr__(self) -> str:
    return self.to_str()

def indentation(indent: int = 0):
  return "  " * indent

def ensure_dir(dir: str) -> str:
  if not os.path.exists(dir):
    os.makedirs(dir)
  return dir

class Cache:
  def __init__(self) -> None:
    self.index: dict[str, typing.Any] = {}

  def path(self, ID) -> str:
    directory = ".cache"
    if not os.path.exists(directory):
      os.makedirs(directory)
    return os.path.join(directory, ID + ".pickle")

  def query(self, ID: str) -> typing.Any:
    if ID in self.index:
      return self.index[ID]
    path = self.path(ID)
    if os.path.exists(path):
      data: typing.Any
      with open(path, "rb") as file:
        data = pickle.load(file)
      self.index[ID] = data
      return data
    return None

  def store(self, ID: str, data: typing.Any):
    path = self.path(ID)
    with open(path, "wb") as file:
      pickle.dump(data, file)
    self.index[ID] = data

class Timer:
  def __init__(self, indent: int = 0) -> None:
    self.clock = time.time()
    self.indent = indent

  def branch(self) -> Timer:
    return Timer(self.indent + 1)

  def round(self, msg: str):
    nclock = time.time()
    diff = nclock - self.clock
    print("%s| %s | Elapsed %s s" % ("  " * self.indent, msg, diff))
    self.clock = time.time()

  def clear(self):
    self.clock = time.time()

def is_reverse_of(A_id: str, B_id: str) -> bool:
  if A_id == '-' + B_id:
    return True
  if '-' + A_id == B_id:
    return True
  return False

def parse_shape(shape_str: str) -> list[Point]:
  points_str = shape_str.split()
  shape: list[Point] = []
  for point_str in points_str:
    x_str, y_str = point_str.split(',')
    shape.append(Point(float(x_str), float(y_str)))
  return shape

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


