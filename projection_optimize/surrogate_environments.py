import os 
dir_path = os.path.dirname(os.path.realpath(__file__))
import gym
import numpy as np
np.random.seed(10)
from gym import spaces
from surrogate_models import coefficient_model, coefficient_model_adjoint

"""
State:
The current vector of chosen values

Action:
choose the next value
"""
class airfoil_surrogate_environment(gym.Env):

    def __init__(self, env_params):
    
        self.num_params = env_params['num_params']
        self.num_obs = env_params['num_obs']
        self.init_guess = env_params['init_guess'] # Needs to be shape=(1,self.num_params)

        # Load dataset
        input_data = np.load(dir_path+'/doe_data.npy').astype('float32')
        output_data = np.load(dir_path+'/coeff_data.npy').astype('float32')

        if env_params['model_type'] == 'regular':
            self.model = coefficient_model(input_data,output_data)
        elif env_params['model_type'] == 'augmented':
            adjoint_data = np.zeros(shape=(170,8)).astype('float32') # placeholder
            self.model = coefficient_model_adjoint(input_data,output_data,adjoint_data)

        # Restore model for use in RL
        self.model.restore_model()

        print('Action parameter dimension : ', self.num_params)
        print('Observation parameter dimension : ', self.num_obs)


        lbo = -10.0*np.ones(shape=2)
        ubo = 10*np.ones(shape=2)
        self.observation_space = spaces.Box(low=lbo,high=ubo,dtype='double')

        lba = -10.0*np.ones(shape=8)
        uba = 10*np.ones(shape=8)
        self.action_space = spaces.Box(low=lba,high=uba,dtype='double')

        # initialization
        self.max_iters = 100
        self.start_coeffs = self.model.predict(self.init_guess.reshape(1,self.num_params))[0,:] # This is the initial observation
        self.coeffs = self.start_coeffs
       
    def reset(self):
        self.shape_vec = self.init_guess
        self.coeffs = self.start_coeffs
        self.iter = 0
        self.path = []
        self.coeffs_path = []
        
        return self.coeffs
        
    def _take_action(self, action):
        self.path.append(self.shape_vec)
        self.shape_vec = action
        self.iter = self.iter + 1
        
    def step(self, action):
    
        self._take_action(action)       
       
        # Need to use surrogate model (NN based) to calculate coefficients
        input_var = self.shape_vec.reshape(1,self.num_params)        
        obs =  self.model.predict(input_var)[0,:]
        pred = self.model.predict(input_var)[0,0]

        self.coeffs = obs
        self.coeffs_path.append(obs)
      
        if self.iter < self.max_iters:
            reward = 1.0-(pred)**2
            done = False
        else:
            reward = 1.0-(pred)**2
            done = True
        
        return obs, reward, done , {}
        
    def render(self, mode="human", close=False):
        pass


if __name__ == '__main__':
    # Create an RL based optimization check
    env_params = {}
    env_params['num_params'] = 8
    env_params['num_obs'] = 2
    env_params['init_guess'] = np.random.uniform(size=(8))
    env_params['model_type'] = 'regular'

    check = airfoil_surrogate_environment(env_params)
    check.reset()
    check.step(np.random.uniform(size=(8)))