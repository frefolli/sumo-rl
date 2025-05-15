#!/usr/bin/env python3
import abc
import os
from sumo_rl.environment.env import SumoEnvironment
from sumo_rl.observations import ObservationFunction
from sumo_rl.rewards import RewardFunction
from sumo_rl.environment.traffic_signal import TrafficSignal
from sumo_rl.agents.agent import Agent
from sumo_rl.agents.ql_agent import QLAgent
from sumo_rl.agents.dqn_agent import DQNAgent
from sumo_rl.agents.ppo_agent import PPOAgent
from sumo_rl.agents.fixed_agent import FixedAgent
from sumo_rl.exploration.epsilon_greedy import EpsilonGreedy
from sumo_rl.util.config import Config

class AgentFactory(abc.ABC):
  def __init__(self, env: SumoEnvironment, config: Config, recycle: bool = False) -> None:
    self.env = env
    self.config = config
    self.recycle: bool = recycle
  
  @abc.abstractmethod
  def agent_by_assignments(self, assignments: dict[str, list[str]]) -> list[Agent]:
    """Abstract function to create agents for given assignments"""
    pass

  @abc.abstractmethod
  def agent(self, agent_id: str, controlled_entities: dict[str, TrafficSignal], *pargs, **kargs) -> Agent:
    """Abstract function to create an agent"""
    pass

class FixedAgentFactory(AgentFactory):
  def __init__(self, env: SumoEnvironment, config: Config, recycle: bool = False, cycle_time: int = 6) -> None:
    super().__init__(env, config, recycle)
    self.cycle_time : int = cycle_time
  
  def agent_by_assignments(self, assignments: dict[str, list[str]]) -> list[Agent]:
    agents = []
    traffic_signals = self.env.traffic_signals
    for agent_id, traffic_signal_ids in assignments.items():
      controlled_entities = {traffic_signal_id: traffic_signals[traffic_signal_id] for traffic_signal_id in traffic_signal_ids}
      agents.append(self.agent(agent_id, controlled_entities))
    return agents

  def agent(self, agent_id: str, controlled_entities: dict[str, TrafficSignal]) -> Agent:
    assert len(controlled_entities) > 0
    a_traffic_signal_id = list(controlled_entities)[0]
    action_space = controlled_entities[a_traffic_signal_id].action_space
    agent = FixedAgent(id=agent_id,
                       controlled_entities=controlled_entities,
                       action_space=action_space,
                       cycle_time=self.cycle_time)
    return agent

class QLAgentFactory(AgentFactory):
  def __init__(self, env: SumoEnvironment, config: Config, alpha, gamma, initial_epsilon, min_epsilon, decay, recycle: bool = False) -> None:
    super().__init__(env, config, recycle)
    self.alpha: float = alpha
    self.gamma: float = gamma
    self.initial_epsilon: float = initial_epsilon
    self.min_epsilon: float = min_epsilon
    self.decay: float = decay
  
  def agent_by_assignments(self, assignments: dict[str, list[str]]) -> list[Agent]:
    agents = []
    traffic_signals = self.env.traffic_signals
    for agent_id, traffic_signal_ids in assignments.items():
      controlled_entities = {traffic_signal_id: traffic_signals[traffic_signal_id] for traffic_signal_id in traffic_signal_ids}
      agents.append(self.agent(agent_id, controlled_entities, self.env.observation_fn, self.env.reward_fn))
    return agents

  def agent(self, agent_id: str,
                  controlled_entities: dict[str, TrafficSignal],
                  observation_fn: ObservationFunction,
                  reward_fn: RewardFunction) -> Agent:
    assert len(controlled_entities) > 0
    a_traffic_signal_id = list(controlled_entities)[0]
    action_space = controlled_entities[a_traffic_signal_id].action_space
    state_space = observation_fn.observation_space(controlled_entities[a_traffic_signal_id])
    agent = QLAgent(id=agent_id,
                   observation_fn=observation_fn,
                   reward_fn=reward_fn,
                   controlled_entities=controlled_entities,
                   state_space=state_space,
                   action_space=action_space,
                   alpha=self.alpha,
                   gamma=self.gamma,
                   exploration_strategy=EpsilonGreedy(initial_epsilon=self.initial_epsilon,
                                                      min_epsilon=self.min_epsilon,
                                                      decay=self.decay))
    if self.recycle:
      agent_memory_file = self.config.agents_file(None, agent_id)
      if os.path.exists(agent_memory_file):
        print("recycle agent %s" % agent_memory_file)
        agent.deserialize(agent_memory_file)
      else:
        print("building agent %s" % agent_memory_file)
    return agent

class DQNAgentFactory(AgentFactory):
  def __init__(self, env: SumoEnvironment, config: Config, recycle: bool = False) -> None:
    super().__init__(env, config, recycle)
  
  def agent_by_assignments(self, assignments: dict[str, list[str]]) -> list[Agent]:
    agents = []
    traffic_signals = self.env.traffic_signals
    for agent_id, traffic_signal_ids in assignments.items():
      controlled_entities = {traffic_signal_id: traffic_signals[traffic_signal_id] for traffic_signal_id in traffic_signal_ids}
      agents.append(self.agent(agent_id, controlled_entities, self.env.observation_fn, self.env.reward_fn))
    return agents

  def agent(self, agent_id: str,
                  controlled_entities: dict[str, TrafficSignal],
                  observation_fn: ObservationFunction,
                  reward_fn: RewardFunction) -> Agent:
    assert len(controlled_entities) > 0
    a_traffic_signal_id = list(controlled_entities)[0]
    action_space = controlled_entities[a_traffic_signal_id].action_space
    state_space = observation_fn.observation_space(controlled_entities[a_traffic_signal_id])
    agent = DQNAgent(id=agent_id,
                     observation_fn=observation_fn,
                     reward_fn=reward_fn,
                     controlled_entities=controlled_entities,
                     state_space=state_space,
                     action_space=action_space)
    if self.recycle:
      agent_memory_file = self.config.agents_file(None, agent_id)
      if os.path.exists(agent_memory_file):
        print("recycle agent %s" % agent_memory_file)
        agent.deserialize(agent_memory_file)
      else:
        print("building agent %s" % agent_memory_file)
    return agent

class PPOAgentFactory(AgentFactory):
  def __init__(self, env: SumoEnvironment, config: Config, recycle: bool = False) -> None:
    super().__init__(env, config, recycle)
  
  def agent_by_assignments(self, assignments: dict[str, list[str]]) -> list[Agent]:
    agents = []
    traffic_signals = self.env.traffic_signals
    for agent_id, traffic_signal_ids in assignments.items():
      controlled_entities = {traffic_signal_id: traffic_signals[traffic_signal_id] for traffic_signal_id in traffic_signal_ids}
      agents.append(self.agent(agent_id, controlled_entities, self.env.observation_fn, self.env.reward_fn))
    return agents

  def agent(self, agent_id: str,
                  controlled_entities: dict[str, TrafficSignal],
                  observation_fn: ObservationFunction,
                  reward_fn: RewardFunction) -> Agent:
    assert len(controlled_entities) > 0
    a_traffic_signal_id = list(controlled_entities)[0]
    action_space = controlled_entities[a_traffic_signal_id].action_space
    state_space = observation_fn.observation_space(controlled_entities[a_traffic_signal_id])
    agent = PPOAgent(id=agent_id,
                     observation_fn=observation_fn,
                     reward_fn=reward_fn,
                     controlled_entities=controlled_entities,
                     state_space=state_space,
                     action_space=action_space)
    if self.recycle:
      agent_memory_file = self.config.agents_file(None, agent_id)
      if os.path.exists(agent_memory_file):
        print("recycle agent %s" % agent_memory_file)
        agent.deserialize(agent_memory_file)
      else:
        print("building agent %s" % agent_memory_file)
    return agent
