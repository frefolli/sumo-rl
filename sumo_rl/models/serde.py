from __future__ import annotations
import abc
import json
import yaml
import pickle
"""
Magic of SerDe
"""

## Dict
class SerdeDict(abc.ABC):
  @abc.abstractmethod
  def to_dict(self) -> dict:
    pass

  @classmethod
  @abc.abstractmethod
  def from_dict(cls, data: dict):
    return data

## JSON
class SerdeJson(SerdeDict):
  def to_json(self) -> str:
    return json.dumps(self.to_dict())

  @classmethod
  def from_json(cls, data: str):
    return cls.from_dict(json.loads(data))

class SerdeJsonFile(SerdeJson):
  def to_json_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_json())

  @classmethod
  def from_json_file(cls, filepath: str):
    with open(filepath, mode="r", encoding="utf-8") as file:
      data = cls.from_json(file.read())
    return data

## XML
class SerdeXML(abc.ABC):
  @abc.abstractmethod
  def to_xml(self, indent: int = 0) -> str:
    pass

class SerdeXMLFile(SerdeXML):
  def to_xml_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_xml())

## D2
class SerdeD2(abc.ABC):
  @abc.abstractmethod
  def to_d2(self, indent: int = 0) -> str:
    pass

class SerdeD2File(SerdeD2):
  def to_d2_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_d2())

## YAML
class SerdeYaml(SerdeDict):
  def to_yaml(self) -> str:
    return yaml.dump(self.to_dict(), Dumper=yaml.Dumper)

  @classmethod
  def from_yaml(cls, data: str):
    return cls.from_dict(yaml.load(data, Loader=yaml.Loader))

class SerdeYamlFile(SerdeYaml):
  def to_yaml_file(self, filepath: str):
    with open(filepath, mode="w", encoding="utf-8") as file:
      file.write(self.to_yaml())

  @classmethod
  def from_yaml_file(cls, filepath: str):
    with open(filepath, mode="r", encoding="utf-8") as file:
      data = cls.from_yaml(file.read())
    return data

## Pickle
class SerdePickleFile:
  def to_pickle_file(self, filepath: str):
    with open(filepath, mode="wb", encoding="utf-8") as file:
      pickle.dump(self, file)

  @classmethod
  def from_pickle_file(cls, filepath: str):
    with open(filepath, mode="rb", encoding="utf-8") as file:
      data = pickle.load(file)
    return data

## Generic

class GenericFile(SerdeYamlFile, SerdeJsonFile):
	def __init__(self, data: dict) -> None:
		self.data = data

	def to_dict(self) -> dict:
		return self.data

	@staticmethod
	def from_dict(data: dict):
		return GenericFile(data)
