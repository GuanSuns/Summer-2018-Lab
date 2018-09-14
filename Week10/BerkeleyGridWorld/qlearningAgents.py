# qlearningAgents.py
# ------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from game import *
from learningAgents import ReinforcementAgent

import random
import util
import math
import numpy as np


class QLearningAgent(ReinforcementAgent):
    """
      Q-Learning Agent

      Functions you should fill in:
        - computeValueFromQValues
        - computeActionFromQValues
        - getQValue
        - getAction
        - update

      Instance variables you have access to
        - self.epsilon (exploration prob)
        - self.alpha (learning rate)
        - self.discount (discount rate)

      Functions you should use
        - self.getLegalActions(state)
          which returns legal actions for a state
    """
    def __init__(self, init_temp=1024.0, temp_decrease_rate=2.0, **args):
        """
            init_temp - the initial temperature used for softmax
            temp_decrease_rate -  the value of softmax temperature decreasing rate
        """
        # you can initialize Q-values here...
        ReinforcementAgent.__init__(self, **args)

        "*** YOUR CODE HERE ***"
        # the key of Q-Values should be (state, action)
        self.qValues = util.Counter()
        self.temperatures = dict()
        self.init_temp = init_temp
        self.temp_decrease_rate = temp_decrease_rate
        self.is_show_real_values = True
        #############################################################
        ##############  VDBE epsilon annealing   ####################
        #############################################################
        self.use_VDBE = False
        self.state_VDBE = dict()
        self.VDBE_sigma = 0.05
        self.VDBE_delta = 0.1
        self.episode_anneal_threshold = 0.15
        #############################################################
        ############  Episode-wise epsilon annealing   ##############
        #############################################################
        self.use_episode_epsilon_anneal = False
        self.global_epsilon = 0     # current best: 0.3
        self.global_min_epsilon = 0     # current best: 0.1
        self.global_decay_rate = 1.0 + 0.001  # Mean lifetime is 695
        self.episode_init_epsilon = 1.0
        self.episode_decay_rate = 1.0 + 0.6   # episode decay rate (mean lifetime - 0.1: 9, 0.2: 5; 0.3: 4)
        self.episode_epsilon = 1.0
        #############################################################
        #############################################################

    def startEpisode(self):
        ReinforcementAgent.startEpisode(self)
        self.episode_epsilon = self.episode_init_epsilon

    def showRealValues(self):
        self.is_show_real_values = True

    def hideRealValues(self):
        self.is_show_real_values = False

    def getQValues(self):
        return self.qValues

    def getQValuesCopy(self):
        return self.qValues.copy()

    def getQValue(self, state, action):
        """
          Returns Q(state,action)
          Should return 0.0 if we have never seen a state
          or the Q node value otherwise
        """
        "*** YOUR CODE HERE ***"
        # return 0 if hide-values is set and the state is not an exiting state
        if (not self.is_show_real_values) and (action != 'exit'):
            return 0

        return self.qValues[(state, action)]

    def computeValueFromQValues(self, state):
        """
          Returns max_action Q(state,action)
          where the max is over legal actions.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return a value of 0.0.
        """
        "*** YOUR CODE HERE ***"
        actions = self.getLegalActions(state)
        if len(actions) == 0:
            return 0

        maxQValue = float("-inf")
        for action in actions:
            qValue = self.getQValue(state, action)
            if qValue > maxQValue:
                maxQValue = qValue
        return maxQValue

    def computeActionFromQValues(self, state):
        """
          Choose the action using softmax function
          epsilon >= 0: use e-greedy
          epsilon < 0: use softmax
        """
        "*** YOUR CODE HERE ***"
        # Get current temperature
        temperature = self.getTemperature(state)
        # update temperature
        self.updateTemperature(state)

        actions = self.getLegalActions(state)
        if len(actions) == 0:
            return None

        qValues = list()
        for action in actions:
            qValue = float(self.getQValue(state, action))
            qValues.append(qValue)
        maxQValue = np.max(qValues)

        # if epsilon < 0: use softmax
        if self.epsilon < 0:
            softmaxValues = np.exp((qValues - maxQValue) / temperature) \
                            / float(np.sum(np.exp((qValues - maxQValue) / temperature)))
            actionId = np.random.choice(np.arange(0, len(actions)), p=softmaxValues)
        # if epsilon >= 0: choose the best action
        else:
            actionId = np.random.choice(np.flatnonzero(maxQValue == qValues))

        return actions[actionId]

    def updateTemperature(self, state):
        """ safely update the temperature for softmax """
        if state in self.temperatures:
            old_temperature = self.temperatures[state]
            # only update the temperature when it's not less than 0.5
            if old_temperature > 0.5:
                self.temperatures[state] = old_temperature / float(self.temp_decrease_rate)
        else:
            self.temperatures[state] = self.init_temp

    def getTemperature(self, state):
        """ return the temperature value of the state """
        if state in self.temperatures:
            return self.temperatures[state]
        else:
            self.temperatures[state] = self.init_temp
            return self.init_temp

    def getAction(self, state):
        """
          Compute the action to take in the current state.  With
          probability self.epsilon, we should take a random action and
          take the best policy action otherwise.  Note that if there are
          no legal actions, which is the case at the terminal state, you
          should choose None as the action.

          HINT: You might want to use util.flipCoin(prob)
          HINT: To pick randomly from a list, use random.choice(list)
        """
        # Pick Action
        legalActions = self.getLegalActions(state)
        # if there is no legal action
        if len(legalActions) == 0:
            return None

        # choose an action
        action = self.computeActionFromQValues(state)
        # if epsilon > 0, use epsilon-greedy
        # flip coin with probability of self.epsilon to determine whether to take random action
        if not self.use_VDBE \
                and not self.use_episode_epsilon_anneal \
                and self.epsilon > 0 \
                and util.flipCoin(self.epsilon):
            action = random.choice(legalActions)
        # if use_VDBE is set
        elif self.use_VDBE:
            if state in self.state_VDBE:
                prob = self.state_VDBE[state]
                # check whether to use episode-wise epsilon annealing
                if prob < self.episode_anneal_threshold \
                        and prob < self.episode_epsilon \
                        and self.use_episode_epsilon_anneal:
                    prob = self.episode_epsilon
                if util.flipCoin(prob):
                    action = random.choice(legalActions)
        # if only use episode-wise epsilon annealing
        elif self.use_episode_epsilon_anneal and util.flipCoin(self.episode_epsilon):
            action = random.choice(legalActions)

        return action

    def getCurrentBestActions(self, state, is_single_action=False):
        """
        Choose the optimal action without any randomness
        """
        actions = np.array(self.getLegalActions(state))
        if len(actions) == 0:
            return None

        qValues = list()
        for action in actions:
            qValue = float(self.getQValue(state, action))
            qValues.append(qValue)
        maxQValue = np.max(qValues)

        action_indices = np.flatnonzero(qValues == maxQValue)
        if is_single_action:
            action_indices = random.choice(action_indices)
        return actions[action_indices]

    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """
        "*** YOUR CODE HERE ***"
        oldQValue = self.getQValue(state, action)
        nextStateValue = self.computeValueFromQValues(nextState)

        newQValue = (1-self.alpha)*oldQValue + self.alpha*(reward + self.discount*nextStateValue)
        self.qValues[(state, action)] = newQValue

        # update VDBE
        if self.use_VDBE:
            self.updateVDBE(state, oldQValue, newQValue)
        # update episode-wise epsilon annealing
        if self.use_episode_epsilon_anneal:
            self.updateEpisodeEpsilonAnnealing()

    def updateEpisodeEpsilonAnnealing(self):
        self.global_epsilon = max(self.global_epsilon/self.global_decay_rate, self.global_min_epsilon)
        self.episode_epsilon = max(self.episode_epsilon/self.episode_decay_rate, self.global_epsilon)

    def updateVDBE(self, state, old_qValue, new_qValue):
        # check if VDBE value for current state has been initialized
        if state not in self.state_VDBE:
            self.state_VDBE[state] = 1.0
        qValue_error = np.fabs(float(new_qValue) - float(old_qValue))
        f = (1.0 - np.exp((-qValue_error)/self.VDBE_sigma)) / (1.0 + np.exp((-qValue_error)/self.VDBE_sigma))
        self.state_VDBE[state] = self.VDBE_delta * f + (1 - self.VDBE_delta) * self.state_VDBE[state]

    def getPolicy(self, state):
        return self.getCurrentBestActions(state, is_single_action=True)

    def getValue(self, state):
        return self.computeValueFromQValues(state)

    @staticmethod
    def getAgentType():
        return 'qLearningAgent'


class TamerQAgent(QLearningAgent):
    def __init__(self, max_n_experiences=1000, window_size=1, is_asyn_input=True
                 , init_temp=1024.0, temp_decrease_rate=2.0, **args):
        """
            window_size: use the experiences within 2 seconds to update the weights
            max_n_experiences: maximum number of experiences stored in the history list

            Instance variables inherited from QLearningAgent
                - self.epsilon (exploration prob)
                - self.alpha (learning rate)
                - self.discount (discount rate)
            init_temp - the initial temperature used for softmax
            temp_decrease_rate -  the value of softmax temperature decreasing rate
            is_asyn_input - whether to wait for human feedback after taking an action
        """
        QLearningAgent.__init__(self, init_temp=init_temp
                                , temp_decrease_rate=temp_decrease_rate, **args)

        # initialize experiences list
        self.max_n_experiences = max_n_experiences
        self.experiences = list()
        self.window_size = window_size
        self.is_asyn_input = is_asyn_input

    def receiveHumanSignal(self, human_signal):
        """ receive human signal and update the weights """
        # do nothing when the signal is 0 or it's not in training
        if human_signal == 0:
            return

        # just for fun, update episode-wise epsilon annealing
        if self.use_episode_epsilon_anneal:
            self.updateEpisodeEpsilonAnnealing()

        # if pause-and-wait-for-user-feedback, only update according to the latest observation
        if not self.is_asyn_input:
            if len(self.experiences) > 0:
                # get the latest experience
                experience = self.experiences[len(self.experiences)-1]

                # do the update
                action = experience['action']
                state = experience['state']
                oldQValue = self.qValues[(state, action)]
                newQValue = oldQValue + self.alpha * (human_signal - oldQValue)
                self.qValues[(state, action)] = newQValue

                # clear experiences
                self.experiences = list()

        else:
            # clear stale data
            current_time = time.time()
            while len(self.experiences) > 0:
                experience = self.experiences[0]
                if experience['time'] < current_time - self.window_size:
                    self.experiences.pop(0)
                else:
                    break

            # update q-values
            alpha = self.alpha
            for experience in self.experiences:
                action = experience['action']
                state = experience['state']
                oldQValue = self.qValues[(state, action)]
                newQValue = oldQValue + alpha * (human_signal - oldQValue)
                self.qValues[(state, action)] = newQValue

            # clear experiences
            self.experiences = list()

    def update(self, state, action, nextState, reward):
        """
          Add the transition experience to experiences list
        """
        "*** YOUR CODE HERE ***"
        current_time = time.time()
        experience = {'time': current_time, 'action': action, 'state': state, 'nextState': nextState, 'reward': reward}
        self.experiences.append(experience)

        # pop out stale experience
        while len(self.experiences) > self.max_n_experiences:
            self.experiences.pop(0)

    @staticmethod
    def getAgentType():
        return 'TamerAgent'
