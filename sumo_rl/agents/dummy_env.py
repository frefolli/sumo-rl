import gymnasium

class DummyEnv(gymnasium.Env):
    """A dummy environment just to initialize a Stable-Baselines RL model."""
    def __init__(self, observation_space, action_space):
        super().__init__()
        self.observation_space = observation_space
        self.action_space = action_space
    
    def reset(self):
        return self.observation_space.sample()
    
    def step(self, _):
        return self.observation_space.sample(), 0, False, {}
