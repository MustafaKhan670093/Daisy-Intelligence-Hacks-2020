import gym
import numpy as np
import random
import matplotlib.pyplot as plt
from site_location_copy import SiteLocationPlayer

DEFAULT_CONFIGURATION = {
    "map_size": (400, 400),
    "population": 1e6,
    "n_rounds": 10,
    "starting_cash": 70000,
    "profit_per_customer": 0.5,
    "max_stores_per_round": 2,
    "place_stores_time_s": 10,
    "ignore_player_exceptions": True,
    "store_config": {
        "small": {
            "capital_cost": 10000.0,
            "operating_cost": 1000.0,
            "attractiveness": 25.0,
            "attractiveness_constant": 1.0,
        },
        "medium": {
            "capital_cost": 50000.0,
            "operating_cost": 2000.0,
            "attractiveness": 50.0,
            "attractiveness_constant": 1.0,
        },
        "large": {
            "capital_cost": 100000.0,
            "operating_cost": 3000.0,
            "attractiveness": 100.0,
            "attractiveness_constant": 1.0
        },
    }
}

class RetailSpace(gym.Env):
    def __init__(self, grid_width=400, grid_height=400, stochastic_actions_probability=1.0/3.0, config: Dict, population=1000000, size):
        super(RetailSpace, self).__init__()
        
        self.size = size
        self.population = population

        self.grid_width = grid_width
        self.grid_height = grid_height

        self.player_id = player_id
        self.config = config

        #self.name = f"{self.__class__.__name__}-{self.player_id}"
        #self.color = self._get_color()
        self.stores_placed= []

        noise = generate_perlin_noise_2d(size, 
                                         (4, 4), 
                                         (False, False))
        noise = np.where(noise < 0, 0, noise)
        noise *= population / np.sum(noise)

        self.population_distribution = noise
        self.current_funds = 70000
        self.step_count = 0

    def step_count(self):
        return self.stepCount

    # def step(self, action):
    #     return np.array(self.currentState), reward, done, {}

    def step(self, desired_action):
        self.step_count += 1
        action = self.determine_which_action_will_actually_occur(desired_action)
        desired_new_state = self.calculate_desired_new_state(action)
        if not self.is_a_wall(desired_new_state):
            self.move_user(self.current_user_location, desired_new_state)
        self.next_state = [self.location_to_state(self.current_user_location), self.desired_goal[0]]

        if self.user_at_goal_location():   ### Add ending conditions or condition to increase reward
            self.reward = self.reward_for_achieving_goal
            #self.done = True
        else:
            self.reward = self.step_reward_for_not_achieving_goal
            if self.step_count >= self.max_episode_steps: self.done = True
            else: self.done = False
        self.achieved_goal = self.next_state[:self.state_only_dimension]
        self.state = self.next_state

        if self.random_goal_place:
            self.s = {"observation": np.array(self.next_state[:self.state_only_dimension]),
                "desired_goal": np.array(self.desired_goal),
                "achieved_goal": np.array(self.achieved_goal)}
        else:
            self.s = np.array(self.next_state[:self.state_only_dimension])

        return self.s, self.reward, self.done, {}

    def determine_which_action_will_actually_occur(self, desired_action):
        """Chooses what action will actually occur. Gives 1. - self.stochastic_actions_probability chance to the
        desired action occuring and the rest of probability spread equally among the other actions"""
        if random.random() < self.stochastic_actions_probability:
            valid_actions = [action for action in self.actions if action != desired_action]
            action = random.choice(valid_actions)
        else: action = desired_action
        return action

    def reset(self):
        self.stepCount = 0
        #self.currentState = np.array([8, 1], dtype=np.int32)
        self.current_funds = 70000
        self.stores_placed = []
        
        return np.array(self.currentState)

    def is_on_obstacle(self, i, j):
        if 0 <= i < self.map.shape[0] and 0 <= j < self.map.shape[1]:
            return self.map[i, j] == 0
        return True
    def close(self):
        pass

    def seed(self):
        pass

    def render(self, mode='human'):
        pass

    def render_traj(self, stateSet, ax):
        idx, idy = np.where(self.map == 0)
        ax.scatter(idx, idy, c='black', marker='s', s=5)
        ax.set_xlim([-1, self.map.shape[0] + 1])
        ax.set_ylim([-1, self.map.shape[1] + 1])
        ax.scatter(self.targetState[0], self.targetState[1], c='green', marker='s', s=10)

        traj = np.array(stateSet)
        ax.plot(traj[:,0], traj[:,1])


    def plot_map(self, ax):
        idx, idy = np.where(self.map == 0)
        ax.scatter(idx, idy, c='black', marker='s', s = 10)
        ax.set_xlim([-1, self.map.shape[0] + 1])
        ax.set_ylim([-1, self.map.shape[1] + 1])
        ax.scatter(self.targetState[0], self.targetState[1], c='green', marker='s', s = 10 )

