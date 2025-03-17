from sumo_rl.models.commons import Point
import sumo_rl.models.sumo

MIN_GAP = 2.5
VEHICLE_LENGTH = 5.0
TAU = 1.0

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
  def __init__(self, id: str, from_junction: str, to_junction: str, lanes: list[Lane], shape: list[Point]) -> None:
    self.id: str = id
    self.from_junction: str = from_junction
    self.to_junction: str = to_junction
    self.lanes: list[Lane] = lanes
    self.shape: list[Point] = shape

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
