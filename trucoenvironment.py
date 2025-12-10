import random
from environments import SimulatedEnvironment

# Valores de las cartas
CARD_VALUES = {
    ('Espada', 1): 14, ('Basto', 1): 13, ('Espada', 7): 12, ('Oro', 7): 11,
    ('Espada', 3): 10, ('Basto', 3): 10, ('Oro', 3): 10, ('Copa', 3): 10,
    ('Espada', 2): 9, ('Basto', 2): 9, ('Oro', 2): 9, ('Copa', 2): 9,
    ('Oro', 1): 8, ('Copa', 1): 8,
    ('Espada', 12): 7, ('Basto', 12): 7, ('Oro', 12): 7, ('Copa', 12): 7,
    ('Espada', 11): 6, ('Basto', 11): 6, ('Oro', 11): 6, ('Copa', 11): 6,
    ('Espada', 10): 5, ('Basto', 10): 5, ('Oro', 10): 5, ('Copa', 10): 5,
    ('Basto', 7): 4, ('Copa', 7): 4,
    ('Espada', 6): 3, ('Basto', 6): 3, ('Oro', 6): 3, ('Copa', 6): 3,
    ('Espada', 5): 2, ('Basto', 5): 2, ('Oro', 5): 2, ('Copa', 5): 2,
    ('Espada', 4): 1, ('Basto', 4): 1, ('Oro', 4): 1, ('Copa', 4): 1,
}

class Card:
    def __init__(self, suit, number):
        self.suit = suit
        self.number = number
        self.power = CARD_VALUES.get((suit, number), 0)

    def __str__(self):
        return f"{self.number} de {self.suit}"

class TrucoEnvironment(SimulatedEnvironment):
    def __init__(self):
        super(TrucoEnvironment, self).__init__()
        self._deck = []
        self._hands = {} 
        self._table_cards = [] 
        self._scores = {}
        self._turn_order = []
        
        self._dealer_index = -1       
        self._mano_player_id = None   
        self._round_history = []      
        self._game_over = False
        self._current_round_number = 1
        
        self._agent_names = {}

    @property
    def game_over(self):
        """Propiedad pública para chequear desde el main si terminó el juego"""
        return self._game_over

    def set_agent_name(self, agent_id: int, name: str):
        self._agent_names[agent_id] = name

    def _get_name(self, agent_id):
        return self._agent_names.get(agent_id, f"J-{str(agent_id)[:4]}")

    def _create_deck(self):
        suits = ['Espada', 'Basto', 'Oro', 'Copa']
        numbers = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        deck = [Card(s, n) for s in suits for n in numbers]
        random.shuffle(deck)
        return deck

    def add(self, agent_id: int) -> None:
        super().add(agent_id)
        self._hands[agent_id] = []
        self._scores[agent_id] = 0
        self._turn_order.append(agent_id)
        
        if len(self._turn_order) == 2:
            self._dealer_index = random.randrange(len(self._turn_order))
            self._start_new_hand()

    def _start_new_hand(self):
        if any(s >= 15 for s in self._scores.values()):
            self._game_over = True
            self._update_all_buffers() # Actualizar final
            return

        if self._dealer_index != -1 and self._hands:
             self._dealer_index = (self._dealer_index + 1) % len(self._turn_order)
        
        mano_index = (self._dealer_index + 1) % len(self._turn_order)
        self._mano_player_id = self._turn_order[mano_index]

        self._deck = self._create_deck()
        self._table_cards = []
        self._round_history = [] 
        self._current_round_number = 1 
        
        for agent_id in self._turn_order:
            self._hands[agent_id] = [self._deck.pop() for _ in range(3)]
        
        self._current_turn_id = self._mano_player_id
        self._update_all_buffers()

    def get_property(self, agent_id: int, property_name: str) -> dict:
        if agent_id not in self._agents:
            return {}
        
        response = {"agent": agent_id}
        
        if property_name == "hand":
            response["hand"] = [(c.number, c.suit) for c in self._hands[agent_id]]
        elif property_name == "table":
            response["table"] = [{"agent": self._get_name(aid), "card": str(c)} for aid, c in self._table_cards]
        elif property_name == "is_my_turn":
            response["is_my_turn"] = (agent_id == self._current_turn_id) and not self._game_over
        
        return response

    def take_action(self, agent_id: int, action_name: str, params: dict = {}) -> None:
        if self._game_over or self._current_turn_id != agent_id:
            return

        if action_name == "play_card":
            self._play_card(agent_id, params.get("index"))
        
        self._update_all_buffers()

    def _play_card(self, agent_id, card_index):
        hand = self._hands[agent_id]
        if 0 <= card_index < len(hand):
            card = hand.pop(card_index)
            self._table_cards.append((agent_id, card))
            
            players_count = len(self._turn_order)
            current_idx = self._turn_order.index(agent_id)
            next_player = self._turn_order[(current_idx + 1) % players_count]
            
            if len(self._table_cards) < players_count:
                self._current_turn_id = next_player
            else:
                self._resolve_round_winner()
        else:
            pass

    def _resolve_round_winner(self):
        p1_id, c1 = self._table_cards[0]
        p2_id, c2 = self._table_cards[1]
        
        winner_id = None
        if c1.power > c2.power: winner_id = p1_id
        elif c2.power > c1.power: winner_id = p2_id
        
        self._round_history.append(winner_id)
        self._table_cards = [] 
        
        hand_winner = self._check_hand_winner()
        
        if hand_winner is not None:
            self._scores[hand_winner] += 1
            self._start_new_hand()
        else:
            self._current_round_number += 1
            if winner_id is not None:
                self._current_turn_id = winner_id
            else:
                self._current_turn_id = self._mano_player_id

    def _check_hand_winner(self):
        history = self._round_history
        if len(history) == 1: return None

        if len(history) == 2:
            r1, r2 = history[0], history[1]
            if r1 is not None and r1 == r2: return r1
            if r1 is None and r2 is not None: return r2
            if r2 is None and r1 is not None: return r1
            return None

        if len(history) == 3:
            r1, r2, r3 = history[0], history[1], history[2]
            if r3 is not None: return r3
            if r3 is None:
                if r1 is None and r2 is None: return self._mano_player_id 
                if r1 is not None: return r1 
        return None

    def _update_all_buffers(self):
        scores_named = {self._get_name(aid): score for aid, score in self._scores.items()}
        
        history_named = []
        nombres_rondas = ["1ra", "2da", "3ra"]
        for i, res in enumerate(self._round_history):
            ganador = self._get_name(res) if res is not None else "Parda"
            history_named.append(f"{nombres_rondas[i]}:{ganador}")

        table_named = [f"{self._get_name(pid)}: {str(c)}" for pid, c in self._table_cards]
        mano_name = self._get_name(self._mano_player_id)
        
        # >>> NUEVO: Determinamos nombre de quien tiene el turno actual
        current_turn_name = self._get_name(self._current_turn_id)

        # >>> NUEVO: Determinamos nombre del ganador del partido
        match_winner_name = None
        if self._game_over:
            # Buscamos quien tiene >= 15
            for aid, score in self._scores.items():
                if score >= 15:
                    match_winner_name = self._get_name(aid)
                    break

        for entry in self._statebuffers:
            agent_id = entry["agent_id"]
            buffer = entry["statebuffer"]
            
            state = {
                "hand": [str(c) for c in self._hands.get(agent_id, [])],
                "table": table_named,
                "scores": scores_named,
                "mano_name": mano_name,
                "current_turn_name": current_turn_name, # <--- Info para mensaje "Esperando a X"
                "round_history": history_named,
                "round_num": self._current_round_number,
                "match_winner_name": match_winner_name, # <--- Info para fin de juego
                "my_turn": (self._current_turn_id == agent_id) and not self._game_over,
                "game_over": self._game_over
            }
            buffer.update(state)