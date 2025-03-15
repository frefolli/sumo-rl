from __future__ import annotations
import abc
import json
"""
Magic of SerDe
"""

class SerdeDict(abc.ABC):
  @abc.abstractmethod
  def to_dict(self) -> dict:
    pass

  @staticmethod
  @abc.abstractmethod
  def from_dict(data: dict) -> SerdeDict:
    pass

class SerdeJson(SerdeDict):
  def to_json(self) -> str:
    return json.dumps(self.to_dict())

  @classmethod
  def from_json(cls, data: str) -> SerdeJson:
    return cls.from_dict(json.loads(data))

class SerdeJsonFile(SerdeJson):
  def to_json_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_json())

  @classmethod
  def from_json_file(cls, filepath: str) -> SerdeJsonFile:
    with open(filepath, mode="r", encoding="utf-8") as file:
      return cls.from_json(file.read())

class SerdeXML(abc.ABC):
  @abc.abstractmethod
  def to_xml(self, indent: int = 0) -> str:
    pass

class SerdeXMLFile(SerdeXML):
  def to_xml_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_xml())
