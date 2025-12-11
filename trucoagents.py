import random
import time
from agents import Agent
from environments import SimulatedSensor, SimulatedActuator, SimulatedEnvironment

# --- Sensores ---
class HandSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "hand").get("hand", [])

class TableSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "table").get("table", [])

class GameStateSensor(SimulatedSensor):
    def sense(self): return self._env.get_property(self._agent.id, "game_state")

class TrucoActuator(SimulatedActuator):
    def act(self, action_name, params={}):
        # action_name puede ser: "play_card", "truco", "quiero", etc.
        self._env.take_action(self._agent.id, action_name, params)

# Agente Base 
class TrucoAgent(Agent):
    def __init__(self, env: SimulatedEnvironment):
        super().__init__()
        env.add(self.id)
        self.add_sensor("hand", HandSensor(env))
        self.add_sensor("table", TableSensor(env))
        self.add_sensor("state", GameStateSensor(env)) # Nuevo sensor
        
        actuator = TrucoActuator(env)
        actuator.agent = self
        self.add_actuator("player", actuator)
        
        # Vincular sensores
        self._sensors["hand"].agent = self
        self._sensors["table"].agent = self
        self._sensors["state"].agent = self

    def _perceive(self):
        return {
            "hand": self._sensors["hand"].sense(),
            "table": self._sensors["table"].sense(),
            "game_state": self._sensors["state"].sense()
        }

    def _act(self, percept):
        state = percept["game_state"]
        # Solo actuamos si es nuestro turno
        if state.get("is_my_turn", False):
            action = self.function(percept)
            if action:
                name = action["name"]
                params = action.get("params", {})
                self._actuators["player"].act(name, params)
    
    def behave(self):
        self._act(self._perceive())

# --- Agente Aleatorio (Bot) ---
class RandomTrucoAgent(TrucoAgent):
    def function(self, percept):
        time.sleep(1.0) 
        state = percept["game_state"]
        legal_actions = state.get("legal_actions", [])
        hand = percept["hand"]
        
        if not legal_actions:
            return None

        # Estrategia: elegir aleatoriamente entre todas las acciones legales con igual probabilidad
        # Si hay play_card, expandimos las opciones por cada carta
        
        expanded_actions = []
        for action in legal_actions:
            if action == "play_card":
                # Agregar una opción por cada carta
                for i in range(len(hand)):
                    expanded_actions.append(("play_card", i))
            else:
                expanded_actions.append((action, None))
        
        if not expanded_actions:
            return None
        
        # Elegir aleatoriamente
        chosen = random.choice(expanded_actions)
        action_name = chosen[0]
        action_param = chosen[1]
        
        # Formatear retorno
        if action_name == "play_card":
            carta = hand[action_param]
            print(f"\n[BOT] Juega carta: {carta[0]} de {carta[1]}")
            return {"name": "play_card", "params": {"index": action_param}}
        else:
            print(f"\n[BOT] Dice: ¡{action_name.upper()}!")
            return {"name": action_name}
            
        return None

# --- Agente Manual (Usuario) ---
class ManualTrucoAgent(TrucoAgent):
    def function(self, percept):
        time.sleep(0.5)
        state = percept["game_state"]
        legal = state.get("legal_actions", [])
        hand = percept["hand"]
        
        print("\n" + "*"*30)
        print(" TU TURNO. Opciones:")
        
        options_map = {}
        idx_counter = 1
        
        # Listar opciones
        for action in legal:
            if action == "play_card":
                for i, card in enumerate(hand):
                    print(f" {idx_counter}. Jugar {card[0]} de {card[1]}")
                    options_map[idx_counter] = ("play_card", {"index": i})
                    idx_counter += 1
            elif action == "irse_al_mazo":
                print(f" {idx_counter}. IRSE AL MAZO (Abandonar la mano)")
                options_map[idx_counter] = (action, {})
                idx_counter += 1
            else:
                print(f" {idx_counter}. Cantar/Decir {action.upper()}")
                options_map[idx_counter] = (action, {})
                idx_counter += 1
                
        print("*"*30)
        
        while True:
            try:
                user_input = input(">> Elige opción (número): ")
                choice = int(user_input)
                if choice in options_map:
                    name, params = options_map[choice]
                    return {"name": name, "params": params}
                else:
                    print("Opción inválida.")
            except ValueError:
                print("Ingresa un número.")