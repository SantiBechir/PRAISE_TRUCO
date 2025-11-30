import random
from agents import Agent
from environments import SimulatedSensor, SimulatedActuator
from trucoworld import TrucoEnvironment


class TrucoSensor(SimulatedSensor):
    def __init__(self, e: TrucoEnvironment):
        super(TrucoSensor, self).__init__(e)
    
    def sense(self):
        percept = {}
        percept["hand"] = self._env.get_property(self._agent.id, "hand")["hand"]
        percept["played_cards"] = self._env.get_property(self._agent.id, "played_cards")["played_cards"]
        percept["current_player"] = self._env.get_property(self._agent.id, "current_player")["current_player"]
        percept["scores"] = self._env.get_property(self._agent.id, "scores")["scores"]
        percept["round_winners"] = self._env.get_property(self._agent.id, "round_winners")["round_winners"]
        percept["game_over"] = self._env.get_property(self._agent.id, "game_over")["game_over"]
        percept["valid_actions"] = self._env.get_property(self._agent.id, "valid_actions")["valid_actions"]
        return percept


class TrucoActuator(SimulatedActuator):
    def __init__(self, e: TrucoEnvironment):
        super(TrucoActuator, self).__init__(e)
    
    def act(self, action: str, params: dict = {}):
        self._env.take_action(self._agent.id, action, params)


class TrucoAgent(Agent):
    def __init__(self):
        super(TrucoAgent, self).__init__()
    
    def _perceive(self):
        return self._sensors["sensor"].sense()
    
    def _act(self, action):
        if action:
            self._actuators["actuator"].act(action)
    
    def behave(self):
        percept = self._perceive()
        action = self.function(percept)
        self._act(action)
    
    def function(self, percept):
        pass


class RandomTrucoAgent(TrucoAgent):
    def __init__(self):
        super(RandomTrucoAgent, self).__init__()
    
    def function(self, percept):
        if percept["game_over"]:
            return None
        
        if percept["current_player"] != self.id:
            return None
        
        valid_actions = percept["valid_actions"]
        if not valid_actions:
            return None
        
        play_card_actions = [a for a in valid_actions if a.startswith("play_card_")]
        
        if play_card_actions and random.random() > 0.3:
            return random.choice(play_card_actions)
        
        return random.choice(valid_actions)


class HumanTrucoAgent(TrucoAgent):
    def __init__(self):
        super(HumanTrucoAgent, self).__init__()
        self._pending_action = None
    
    def set_action(self, action: str):
        self._pending_action = action
    
    def function(self, percept):
        if percept["game_over"]:
            return None
        
        if percept["current_player"] != self.id:
            return None
        
        if self._pending_action:
            action = self._pending_action
            self._pending_action = None
            return action
        
        return None
