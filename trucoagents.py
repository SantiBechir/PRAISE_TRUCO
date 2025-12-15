import random
import time
from agents import Agent

# --- Agente Base ---
class TrucoAgent(Agent):
    def __init__(self, env):
        super().__init__()
        self._env = env
        env.add(self.id)
    
    def _perceive(self):
        """Obtiene la percepción completa del agente"""
        state = self._env.get_property(self.id, "game_state")
        hand = self._env.get_property(self.id, "hand")
        table = self._env.get_property(self.id, "table")
        
        return {
            "hand": hand.get("hand", []),
            "table": table.get("table", []),
            "game_state": state
        }
    
    def _act(self, action):
        """Ejecuta una acción en el environment"""
        if action:
            self._env.take_action(self.id, action["name"], action.get("params", {}))
    
    def behave(self):
        """Comportamiento del agente en cada ciclo"""
        percept = self._perceive()
        # Verificar si es mi turno
        if percept["game_state"].get("is_my_turn", False):
            # Decidir acción
            action = self.function(percept)
            # Ejecutar acción
            self._act(action)


# --- Agente Aleatorio (Bot) ---
class RandomTrucoAgent(TrucoAgent):
    def function(self, percept):
        time.sleep(0.5)
        state = percept["game_state"]
        legal_actions = state.get("legal_actions", [])
        hand = percept["hand"]
        
        if not legal_actions:
            return None
        
        # Expandir acciones (play_card cuenta como múltiples opciones)
        expanded_actions = []
        for action in legal_actions:
            if action == "play_card":
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
        
        if action_name == "play_card":
            return {"name": "play_card", "params": {"index": action_param}}
        else:
            return {"name": action_name}

# --- Agente Manual (Usuario) ---
class ManualTrucoAgent(TrucoAgent):
    def function(self, percept):
        # Este agente no decide automáticamente
        # El renderer manejará el input directamente
        time.sleep(0.1)
        return None