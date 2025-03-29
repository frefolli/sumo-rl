import os
import sys
import argparse
import pandas
import sumo_rl.util.config
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

def nproc(jobs: int|None):
  if jobs is None:
    return os.cpu_count()
  return jobs

def agent_factory_by_option(cli_args, config: sumo_rl.util.config.Config, env: sumo_rl.environment.env.SumoEnvironment) -> sumo_rl.preprocessing.factories.AgentFactory:
  val = cli_args.agent
  if val == 'fixed':
    return sumo_rl.preprocessing.factories.FixedAgentFactory(env, config, recycle=cli_args.recycle)
  if val == 'ql':
    return sumo_rl.preprocessing.factories.QLAgentFactory(env, config,
                                                          config.agents.ql.alpha,
                                                          config.agents.ql.gamma,
                                                          config.agents.ql.initial_epsilon,
                                                          config.agents.ql.min_epsilon,
                                                          config.agents.ql.decay,
                                                          recycle=cli_args.recycle)
  if val == 'dqn':
    return sumo_rl.preprocessing.factories.DQNAgentFactory(env, config, recycle=cli_args.recycle)
  if val == 'ppo':
    return sumo_rl.preprocessing.factories.PPOAgentFactory(env, config, recycle=cli_args.recycle)
  raise ValueError(val)

def partition_by_option(cli_args, env: sumo_rl.environment.env.SumoEnvironment) -> sumo_rl.preprocessing.partitions.Partition:
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

def perform_training(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
  env.set_duration(config.training.seconds)
  for run in range(config.training.runs):
    for episode in range(config.training.episodes):
      for routes_file in config.scenario.training_routes:
        env.sumo_seed += 1
        env._route = routes_file
        print("Training :: Run(%s)/Episode(%s)/Routes(%s)/Seed(%s) :: Starting" % (run, episode, routes_file, env.sumo_seed))
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
        print("Training :: Run(%s)/Episode(%s)/Routes(%s)/Seed(%s) :: Ended" % (run, episode, routes_file, env.sumo_seed))

        # Serialize Metrics
        path = config.training_metrics_file(run, episode)
        pandas.DataFrame(env.metrics).to_csv(path, index=False)

        # Serialize Agents
        for agent in agents:
          if agent.can_be_serialized():
            path = config.agents_file(None, None, agent.id)
            agent.serialize(path)
    # Serialize Agents
    for agent in agents:
      if agent.can_be_serialized():
        path = config.agents_file(None, None, agent.id)
        agent.serialize(path)

def perform_evaluation(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
  env.set_duration(config.evaluation.seconds)
  for run in range(config.evaluation.runs):
    for episode, routes_file in enumerate(config.scenario.evaluation_routes):
      env.sumo_seed += 1
      env._route = routes_file
      print("Evaluation :: Run(%s)/Episode(%s)/Routes(%s)/Seed(%s) :: Starting" % (run, episode, routes_file, env.sumo_seed))
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
      print("Evaluation :: Run(%s)/Episode(%s)/Routes(%s)/Seed(%s) :: Ended" % (run, episode, routes_file, env.sumo_seed))

      # Serialize Metrics
      path = config.evaluation_metrics_file(run, episode)
      pandas.DataFrame(env.metrics).to_csv(path, index=False)

def perform_demo(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
  env.set_duration(config.demo.seconds)
  routes_file = config.scenario.demo_routes[0]
  env.sumo_seed += 1
  env._route = routes_file
  print("Demo :: Routes(%s)/Seed(%s) :: Starting" % (routes_file, env.sumo_seed))
  env.reset()
  for agent in agents:
    agent.reset()
  env.gather_data_from_sumo()
  env.compute_observations()
  # env.compute_rewards()
  # env.compute_metrics()
  for agent in agents:
    if agent.can_observe():
      agent.observe(env.observations)
  while not env.done():
    actions = {}
    print(env.sim_step, end="\r")
    for agent in agents:
      actions.update(agent.act())
    # print(env.observations, actions)
    env.step(action=actions)
    env.gather_data_from_sumo()
    env.compute_observations()
    # env.compute_rewards()
    # env.compute_metrics()
    for agent in agents:
      if agent.can_observe():
        agent.observe(env.observations)
  print("Demo :: Routes(%s)/Seed(%s) :: Ended" % (routes_file, env.sumo_seed))

def show_args(cli_args):
  print("Calling with ", {
    'cli_args.agent': cli_args.agent,
    'cli_args.partition': cli_args.partition,
    'cli_args.observation': cli_args.observation,
    'cli_args.reward': cli_args.reward,
    'cli_args.recycle': cli_args.recycle,
    'cli_args.pretend': cli_args.pretend,
    'cli_args.do_training': cli_args.do_training,
    'cli_args.do_evaluation': cli_args.do_evaluation,
    'cli_args.do_demo': cli_args.do_demo
    })

def main():
  cli = argparse.ArgumentParser(sys.argv[0])
  cli.add_argument('-C', '--config', default='./config.yml', help="Selects YAML config (defaults to ./config.yml)")
  cli.add_argument('-A', '--agent', choices=['fixed', 'ql', 'dqn', 'ppo'], default='ql', help="Selects agent type (defaults to ql)")
  cli.add_argument('-P', '--partition', choices=['mono', 'size', 'space'], default='mono', help="Selects partition type (defaults to mono)")
  cli.add_argument('-O', '--observation', choices=['default'], default='default', help="Select observation function (defaults to default)")
  cli.add_argument('-R', '--reward', choices=['dwt', 'as', 'ql', 'p'], default='dwt', help="Select reward function (defaults to dwt)")
  cli.add_argument('-r', '--recycle', action="store_true", default=False, help="If it has to recycle previously trained agents (by means of serialization)")
  cli.add_argument('-p', '--pretend', action="store_true", default=False, help="Don't actually start training and evaluation simulations")
  cli.add_argument('-g', '--use-gui', action="store_true", default=False, help="Uses GUI")
  cli.add_argument('-j', '--jobs', type=int, default=1, nargs='?', help="Uses j number of threads")
  cli.add_argument('-DT', '--do-training', action="store_true", default=False, help="Perform training")
  cli.add_argument('-DE', '--do-evaluation', action="store_true", default=False, help="Perform evaluation")
  cli.add_argument('-DD', '--do-demo', action="store_true", default=False, help="Perform demo")
  cli_args = cli.parse_args(sys.argv[1:])
  show_args(cli_args)
  config: sumo_rl.util.config.Config = sumo_rl.util.config.Config.from_yaml_file(cli_args.config)

  assert ((not cli_args.use_gui) or (os.environ.get("LIBSUMO_AS_TRACI") != '1'))
  assert ((cli_args.use_gui) or (not cli_args.do_demo))

  observation_fn = observation_fn_by_option(cli_args)
  reward_fn = reward_fn_by_option(cli_args)
  env = sumo_rl.environment.env.SumoEnvironment.from_config(config, observation_fn, reward_fn, cli_args.use_gui, nproc(cli_args.jobs))
  agent_factory: sumo_rl.preprocessing.factories.AgentFactory = agent_factory_by_option(cli_args, config, env)
  agents_partition: sumo_rl.preprocessing.partitions.Partition = partition_by_option(cli_args, env)
  agents: list[sumo_rl.agents.Agent] = agent_factory.agent_by_assignments(agents_partition.data)

  if not cli_args.pretend:
    if cli_args.do_training:
      perform_training(config, agents, env)
    if cli_args.do_evaluation:
      perform_evaluation(config, agents, env)
    if cli_args.do_demo:
      perform_demo(config, agents, env)
  env.close()

if __name__ == "__main__":
  main()
