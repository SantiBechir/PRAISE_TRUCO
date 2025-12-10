import random
import time
from agents import Agent
from environments import SimulatedSensor, SimulatedActuator, SimulatedEnvironment

# --- Sensores ---
class HandSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "hand").get("hand", [])
class TableSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "table").get("table", [])
class TurnSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "is_my_turn").get("is_my_turn", False)

# --- Actuador ---
class TrucoActuator(SimulatedActuator):
    def act(self, card_index):
        self._env.take_action(self._agent.id, "play_card", {"index": card_index})

# --- Agente Base ---
class TrucoAgent(Agent):
    def __init__(self, env: SimulatedEnvironment):
        super().__init__()
        env.add(self.id)
        self.add_sensor("hand", HandSensor(env))
        self.add_sensor("table", TableSensor(env))
        self.add_sensor("turn", TurnSensor(env))
        actuator = TrucoActuator(env)
        actuator.agent = self
        self.add_actuator("player", actuator)
        self._sensors["hand"].agent = self
        self._sensors["table"].agent = self
        self._sensors["turn"].agent = self

    def _perceive(self):
        return {
            "hand": self._sensors["hand"].sense(),
            "table": self._sensors["table"].sense(),
            "is_my_turn": self._sensors["turn"].sense()
        }

    def _act(self, percept):
        if percept["is_my_turn"] and percept["hand"]:
            action = self.function(percept)
            if action:
                self._actuators["player"].act(action["index"])
    
    def behave(self):
        self._act(self._perceive())

# --- Agente Aleatorio (Bot) ---
class RandomTrucoAgent(TrucoAgent):
    def function(self, percept):
        time.sleep(1.5) # Piensa un poco
        hand_size = len(percept["hand"])
        if hand_size > 0:
            choice = random.randrange(hand_size)
            # Para debug: muestra qué va a jugar
            carta = percept['hand'][choice]
            print(f"\n[BOT] Juega carta: {carta[0]} de {carta[1]}")
            return {"index": choice}
        return None

# --- Agente Manual (Usuario) ---
class ManualTrucoAgent(TrucoAgent):
    def function(self, percept):
        # >>> CLAVE: Esperamos un poco para que el Renderer dibuje la mesa <<<
        time.sleep(1.0) 
        
        while True:
            try:
                user_input = input(">> Elige índice de carta a jugar: ")
                choice = int(user_input)
                if 0 <= choice < len(percept["hand"]):
                    return {"index": choice}
                else:
                    print("Índice incorrecto.")
            except ValueError:
                print("Ingresa un número.")