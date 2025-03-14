import os
import sys
import argparse
import pandas
import sumo_rl.util.scenario
import sumo_rl.preprocessing.factories
import sumo_rl.preprocessing.partitions
import sumo_rl.observations
import sumo_rl.rewards
import sumo_rl.agents
import sumo_rl.environment.env

if "SUMO_HOME" in os.environ:
  tools = os.path.join(os.environ["SUMO_HOME"], "tools")
  sys.path.append(tools)
else:
  sys.exit("Please declare the environment variable 'SUMO_HOME'")

def agent_factory_by_option(cli_args, scenario: sumo_rl.util.scenario.Scenario, val: str) -> sumo_rl.preprocessing.factories.AgentFactory:
  val = cli_args.agent
  if val == 'fixed':
    return sumo_rl.preprocessing.factories.FixedAgentFactory(env, scenario, recycle=cli_args.recycle)
  if val == 'ql':
    return sumo_rl.preprocessing.factories.QLAgentFactory(env, scenario,
                                                          scenario.config.agent.alpha,
                                                          scenario.config.agent.gamma,
                                                          scenario.config.agent.initial_epsilon,
                                                          scenario.config.agent.min_epsilon,
                                                          scenario.config.agent.decay,
                                                          recycle=cli_args.recycle)
  raise ValueError(val)

def partition_by_option(cli_args, env: str, scenario: sumo_rl.util.scenario.Scenario) -> sumo_rl.preprocessing.partitions.Partition:
  val = cli_args.partition
  if val == 'mono':
    return sumo_rl.preprocessing.partitions.MonadicPartition.Build(env)
  if val == 'size':
    return sumo_rl.preprocessing.partitions.ActionStateSizePartition.Build(env)
  if val == 'space':
    return sumo_rl.preprocessing.partitions.ActionStateSpacePartition.Build(env)
  raise ValueError(val)

def observation_fn_by_option(cli_args) -> sumo_rl.observations.ObservationFunction:
  val = cli_args.observation
  if val == 'default':
    return sumo_rl.observations.DefaultObservationFunction()
  raise ValueError(val)

def reward_fn_by_option(cli_args) -> sumo_rl.rewards.RewardFunction:
  val = cli_args.reward
  if val == 'dwt':
    return sumo_rl.rewards.DiffWaitingTimeRewardFunction()
  if val == 'as':
    return sumo_rl.rewards.AverageSpeedRewardFunction()
  if val == 'ql':
    return sumo_rl.rewards.QueueLengthRewardFunction()
  if val == 'p':
    return sumo_rl.rewards.PressureRewardFunction()
  raise ValueError(val)

def perform_training(scenario: sumo_rl.util.scenario.Scenario, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
    for run in range(scenario.config.training.runs):
      for episode in range(scenario.config.training.episodes):
        print("Training :: Run(%s)/Episode(%s) :: Starting" % (run, episode))
        env.reset()
        for agent in agents:
          agent.reset()
        env.gather_data_from_sumo()
        env.compute_observations()
        env.compute_rewards()
        env.compute_metrics()
        for agent in agents:
          if agent.can_observe():
            agent.observe(env.observations)
        while not env.done():
          actions = {}
          print(env.sim_step, end="\r")
          for agent in agents:
            actions.update(agent.act())
          env.step(action=actions)
          env.gather_data_from_sumo()
          env.compute_observations()
          env.compute_rewards()
          env.compute_metrics()
          for agent in agents:
            if agent.can_observe():
              agent.observe(env.observations)
            if agent.can_learn():
              agent.learn(env.rewards)

        # Serialize Metrics
        path = scenario.training_metrics_file(run, episode)
        pandas.DataFrame(env.metrics).to_csv(path, index=False)

        # Serialize Agents
        for agent in agents:
          if agent.can_be_serialized():
            path = scenario.agents_file(None, None, agent.id)
            agent.serialize(path)
        env.sumo_seed += 1
        print("Training :: Run(%s)/Episode(%s) :: Ended" % (run, episode))

      # Serialize Agents
      for agent in agents:
        if agent.can_be_serialized():
          path = scenario.agents_file(None, None, agent.id)
          agent.serialize(path)

def perform_evaluation(scenario: sumo_rl.util.scenario.Scenario, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
    for run in range(scenario.config.evaluation.runs):
      for episode in range(scenario.config.evaluation.episodes):
        print("Evaluation :: Run(%s)/Episode(%s) :: Starting" % (run, episode))
        env.reset()
        for agent in agents:
          agent.reset()
        env.gather_data_from_sumo()
        env.compute_observations()
        # env.compute_rewards()
        env.compute_metrics()
        for agent in agents:
          if agent.can_observe():
            agent.observe(env.observations)
        while not env.done():
          actions = {}
          print(env.sim_step, end="\r")
          for agent in agents:
            actions.update(agent.act())
          env.step(action=actions)
          env.gather_data_from_sumo()
          env.compute_observations()
          # env.compute_rewards()
          env.compute_metrics()
          for agent in agents:
            if agent.can_observe():
              agent.observe(env.observations)

        # Serialize Metrics
        path = scenario.evaluation_metrics_file(run, episode)
        pandas.DataFrame(env.metrics).to_csv(path, index=False)

        env.sumo_seed += 1
        print("Evaluation :: Run(%s)/Episode(%s) :: Ended" % (run, episode))

def show_args(cli_args):
  print("Calling with ", {
    'cli_args.agent': cli_args.agent,
    'cli_args.partition': cli_args.partition,
    'cli_args.observation': cli_args.observation,
    'cli_args.reward': cli_args.reward,
    'cli_args.recycle': cli_args.recycle,
    'cli_args.pretend': cli_args.pretend
  })

if __name__ == "__main__":
  cli = argparse.ArgumentParser(sys.argv[0])
  sumo_rl.util.scenario.Scenario.add_scenario_selection(cli)
  cli.add_argument('-A', '--agent', choices=['fixed', 'ql'], default='ql', help="Selects agent type (defaults to ql)")
  cli.add_argument('-P', '--partition', choices=['mono', 'size', 'space'], default='mono', help="Selects partition type (defaults to mono)")
  cli.add_argument('-O', '--observation', choices=['default'], default='default', help="Select observation function (defaults to default)")
  cli.add_argument('-R', '--reward', choices=['dwt', 'as', 'ql', 'p'], default='dwt', help="Select reward function (defaults to dwt)")
  cli.add_argument('-r', '--recycle', action="store_true", default=False, help="If it has to recycle previously trained agents (by means of serialization)")
  cli.add_argument('-p', '--pretend', action="store_true", default=False, help="Don't actually start training and evaluation simulations")
  cli_args = cli.parse_args(sys.argv[1:])
  show_args(cli_args)
  scenario = sumo_rl.util.scenario.Scenario(cli_args.scenario)

  assert ((not scenario.config.sumo.use_gui) or (os.environ.get("LIBSUMO_AS_TRACI") != '1'))

  observation_fn = observation_fn_by_option(cli_args)
  reward_fn = reward_fn_by_option(cli_args)
  env = scenario.new_sumo_environment(observation_fn, reward_fn)
  agent_factory: sumo_rl.preprocessing.factories.AgentFactory = agent_factory_by_option(cli_args, scenario, env)
  agents_partition: sumo_rl.preprocessing.partitions.Partition = partition_by_option(cli_args, env, scenario)
  agents: list[sumo_rl.agents.Agent] = agent_factory.agent_by_assignments(agents_partition.data)

  if not cli_args.pretend:
    env.sumo_seed = scenario.config.sumo.sumo_seed
    perform_training(scenario, agents, env)
    perform_evaluation(scenario, agents, env)
  env.close()
