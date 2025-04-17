import os
import sys
import argparse
import pandas
from sumo_rl.models.commons import Timer
from sumo_rl.models.serde import GenericFile, SerdeYamlFile
from sumo_rl.preprocessing.adiacency_graph import build_adiacency_graph
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

def use_selection_of_agent_type():
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

  options = ['fixed', 'ql', 'dqn', 'ppo']
  help_text = """
    Selects the type of Agent to use,
    - fixed: Fixed Cycle agent,
    - ql: Q Learning agent,
    - dqn: Deep Q Learning agent,
    - ppo: Proximal Policy Optimization agent
  """
  return options, help_text, agent_factory_by_option

def use_selection_of_partition():
  def partition_by_option(cli_args, env: sumo_rl.environment.env.SumoEnvironment) -> sumo_rl.preprocessing.partitions.Partition:
    val = cli_args.partition
    if val == 'mono':
      return sumo_rl.preprocessing.partitions.MonadicPartition.Build(env)
    if val == 'size':
      return sumo_rl.preprocessing.partitions.ActionStateSizePartition.Build(env)
    if val == 'space':
      return sumo_rl.preprocessing.partitions.ActionStateSpacePartition.Build(env)
    raise ValueError(val)

  options = ['mono', 'size', 'space']
  help_text = """
    Selects the mechanism for partitioning traffic signals over agents
    - mono: An agent per traffic signal
    - size: Traffic signals are grouped by intersection size (in managed lanes)
    - space: Traffic signals are grouped by observation function space
  """
  return options, help_text, partition_by_option

def use_selection_of_observation_fn():
  def observation_fn_by_option(cli_args) -> sumo_rl.observations.ObservationFunction:
    val = cli_args.observation
    if val == 'default':
      return sumo_rl.observations.DefaultObservationFunction()
    if val == 'sv':
      return sumo_rl.observations.SharedVisionObservationFunction(me_observation=sumo_rl.observations.DefaultObservationFunction(),
                                                                  you_observation=sumo_rl.observations.DefaultObservationFunction())
    if val == 'svp':
      return sumo_rl.observations.SharedVisionObservationFunction(me_observation=sumo_rl.observations.DefaultObservationFunction(),
                                                                  you_observation=sumo_rl.observations.PhaseObservationFunction())
    if val == 'svd':
      return sumo_rl.observations.SharedVisionObservationFunction(me_observation=sumo_rl.observations.DefaultObservationFunction(),
                                                                  you_observation=sumo_rl.observations.DensityObservationFunction())
    if val == 'svq':
      return sumo_rl.observations.SharedVisionObservationFunction(me_observation=sumo_rl.observations.DefaultObservationFunction(),
                                                                  you_observation=sumo_rl.observations.QueueObservationFunction())
    raise ValueError(val)

  options = ['default', 'sv', 'svp', 'svd', 'svq']
  help_text = """
    Selects the observation function to use
    - default: I can see my current phase, if max_green_time has passed, queue lengths and densities of lanes
    - Shared Views: neighbours are defined by a Vision Graph(NODES = Array(Traffic Light),
                                                             EDGES = DICT(Traffic Light: SET(Traffic Light))).
      For now is built seeking for immediately adiancent traffic signals.
      - sv: I can se the `default` state + the `default` state of neighbour traffic signals
      - svp: I can se the `default` state + the phase of neighbour traffic signals
      - svd: I can se the `default` state + the densities of lanes of neighbour traffic signals
      - svq: I can se the `default` state + the queue lengths of lanes of neighbour traffic signals
  """
  return options, help_text, observation_fn_by_option

def use_selection_of_reward_fn():
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

  options = ['dwt', 'as', 'ql', 'p']
  help_text = """
    Selects the reward function to use
    - dwt: Diff Waiting Times
    - as: Average Speeds
    - ql: Average Queue Lengths
    - p: Pressure
  """
  return options, help_text, reward_fn_by_option

def identify_pattern(routes_file_path: str) -> str|None:
  splitted = routes_file_path.split('/')[::-1]
  if len(splitted) >= 3:
    if splitted[2] in ['training', 'evaluation']:
      return splitted[1]
    else:
      print(splitted[2])
  return None

def perform_training(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment, save_intermediate_agents: bool = False):
  timer = Timer()
  env.set_duration(config.training.seconds)
  tracks = {}
  for episode, routes_file in enumerate(config.scenario.training_routes):
    env.sumo_seed += 1
    env.set_route_file(routes_file)
    timer.round("Training :: Episode(%s)/Routes(%s)/Seed(%s) :: Starting" % (episode, routes_file, env.sumo_seed))
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
    timer.round("Training :: Episode(%s)/Routes(%s)/Seed(%s) :: Ended" % (episode, routes_file, env.sumo_seed))

    # Serialize Metrics
    path = config.training_metrics_file(episode)
    pandas.DataFrame(env.metrics).to_csv(path, index=False)
    tracks[path] = identify_pattern(routes_file)

    if save_intermediate_agents:
      # Serialize Agents
      for agent in agents:
        if agent.can_be_serialized():
          path = config.agents_file(episode, agent.id)
          agent.serialize(path)

  # Serialize Agents
  for agent in agents:
    if agent.can_be_serialized():
      path = config.agents_file(None, agent.id)
      agent.serialize(path)
  GenericFile(tracks).to_yaml_file(config.training_metrics_dir() + '/tracks.yml')

def perform_evaluation(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
  timer = Timer()
  env.set_duration(config.evaluation.seconds)
  tracks = {}
  for episode, routes_file in enumerate(config.scenario.evaluation_routes):
    env.sumo_seed += 1
    env.set_route_file(routes_file)
    timer.round("Evaluation :: Episode(%s)/Routes(%s)/Seed(%s) :: Starting" % (episode, routes_file, env.sumo_seed))
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
    timer.round("Evaluation :: Episode(%s)/Routes(%s)/Seed(%s) :: Ended" % (episode, routes_file, env.sumo_seed))

    # Serialize Metrics
    path = config.evaluation_metrics_file(episode)
    pandas.DataFrame(env.metrics).to_csv(path, index=False)
    tracks[path] = identify_pattern(routes_file)
  GenericFile(tracks).to_yaml_file(config.evaluation_metrics_dir() + '/tracks.yml')

def perform_demo(config: sumo_rl.util.config.Config, agents: list[sumo_rl.agents.Agent], env: sumo_rl.environment.env.SumoEnvironment):
  env.set_duration(config.demo.seconds)
  routes_file = config.scenario.demo_routes[-1]
  env.sumo_seed += 1
  env.set_route_file(routes_file)
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
  agent_type_options, agent_type_help, agent_factory_by_option = use_selection_of_agent_type()
  partition_options, partition_help, partition_by_option = use_selection_of_partition()
  observation_fn_options, observation_fn_help, observation_fn_by_option = use_selection_of_observation_fn()
  reward_fn_options, reward_fn_help, reward_fn_by_option = use_selection_of_reward_fn()

  cli = argparse.ArgumentParser(sys.argv[0], description="Experiments with SUMO-RL", formatter_class=argparse.RawTextHelpFormatter)
  cli.add_argument('-C', '--config', default='./config.yml', help="Selects YAML config (defaults to ./config.yml)")
  cli.add_argument('-A', '--agent', choices=agent_type_options, default=agent_type_options[0], help=agent_type_help)
  cli.add_argument('-P', '--partition', choices=partition_options, default=partition_options[0], help=partition_help)
  cli.add_argument('-O', '--observation', choices=observation_fn_options, default=observation_fn_options[0], help=observation_fn_help)
  cli.add_argument('-R', '--reward', choices=reward_fn_options, default=reward_fn_options[0], help=reward_fn_help)
  cli.add_argument('-r', '--recycle', action="store_true", default=False, help="If it has to recycle previously trained agents (by means of serialization)")
  cli.add_argument('-p', '--pretend', action="store_true", default=False, help="Don't actually start training and evaluation simulations")
  cli.add_argument('-g', '--use-gui', action="store_true", default=False, help="Uses GUI")
  cli.add_argument('-j', '--jobs', type=int, default=1, nargs='?', help="Uses j number of threads")
  cli.add_argument('-pa', '--paranoic', action="store_true", default=False, help="Saves ALL intermediate results. you can never say!")
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
  if isinstance(env.observation_fn, sumo_rl.observations.SharedVisionObservationFunction):
    build_adiacency_graph(env, env.observation_fn.vision_graph)
    env.observation_fn.vision_graph.to_d2_file('vision-graph.d2')
  agent_factory: sumo_rl.preprocessing.factories.AgentFactory = agent_factory_by_option(cli_args, config, env)
  agents_partition: sumo_rl.preprocessing.partitions.Partition = partition_by_option(cli_args, env)
  agents: list[sumo_rl.agents.Agent] = agent_factory.agent_by_assignments(agents_partition.data)

  if not cli_args.pretend:
    if cli_args.do_training:
      perform_training(config, agents, env, save_intermediate_agents=cli_args.paranoic)
    if cli_args.do_evaluation:
      perform_evaluation(config, agents, env)
    if cli_args.do_demo:
      perform_demo(config, agents, env)
  env.close()

if __name__ == "__main__":
  main()
