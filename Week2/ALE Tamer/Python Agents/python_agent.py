# python_agent.py
# Author: Lin Guan
#
# The abstract class defined for python agents
# --------------

import utils


class PythonAgent:
    def __init__(self, index=0):
        self.index = index

    def initAgent(self):
        pass

    def getAction(self, state):
        """
            The Agent will receive a GameState and
            must return an action
        """
        utils.raiseNotDefined("getAction")


class PythonReinforcementAgent(PythonAgent):
    def __init__(self, index=0, isTraining=True
                 , epsilon=0.5, alpha=0.5, gamma=1, learning_rate=0.01):
        """
            alpha    - learning rate
            epsilon  - exploration rate
            gamma    - discount factor
            learning_rate   -   learning step size
        """
        PythonAgent.__init__(self, index)
        self.isTraining = isTraining
        self.epsilon = epsilon
        self.learning_rate = alpha
        self.gamma = gamma

    def extract_state(self, rgb_state):
        """ return the state based on current game RGB values"""
        pass

    def addExperience(self, experience):
        """
            Called by environment after
            observing a transition and reward

            experience should be in some format like (state, action, reward)
        """
        utils.raiseNotDefined("addExperience")

    def setIsTraining(self, isTraining):
        self.isTraining = isTraining

    def isInTraining(self):
        return self.isTraining

    def startEpisode(self):
        """
            Called by environment when new episode is starting
        """
        utils.raiseNotDefined("startEpisode")

    def stopEpisode(self):
        """
            Called by environment when episode is done
        """
        utils.raiseNotDefined("stopEpisode")

    def final(self, state):
        """
          Called by environment at the end
        """
        utils.raiseNotDefined("final")




