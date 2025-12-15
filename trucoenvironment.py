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
        
        self._bet_level = 1 
        self._bet_caller_id = None
        self._waiting_response = False
        self._current_turn_id = None
        
        self._agent_names = {}
        self._last_actions = {}  # Trackear última acción de cada jugador
        self._last_log = "Inicio del juego"

    @property
    def game_over(self):
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
            self._update_all_buffers()
            return

        if self._dealer_index != -1 and self._hands:
             self._dealer_index = (self._dealer_index + 1) % len(self._turn_order)
        
        mano_index = (self._dealer_index + 1) % len(self._turn_order)
        self._mano_player_id = self._turn_order[mano_index]

        self._deck = self._create_deck()
        self._table_cards = []
        self._round_history = [] 
        self._current_round_number = 1 
        
        self._bet_level = 1
        self._waiting_response = False
        self._bet_caller_id = None
        
        self._last_log = "--- Nueva Mano ---"

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
        elif property_name == "game_state":
            # Calcular acciones legales para este agente
            legal_actions = []
            is_my_turn = (agent_id == self._current_turn_id) and not self._game_over
            
            if is_my_turn:
                if self._waiting_response:
                    legal_actions = ["quiero", "no_quiero"]
                    if self._bet_level == 2: legal_actions.append("retruco")
                    if self._bet_level == 3: legal_actions.append("vale4")
                else:
                    legal_actions.append("play_card")
                    if self._bet_level == 1: 
                        legal_actions.append("truco")
                
                legal_actions.append("irse_al_mazo")
            
            response["is_my_turn"] = is_my_turn
            response["waiting_response"] = self._waiting_response
            response["current_bet_level"] = self._bet_level
            response["legal_actions"] = legal_actions
            response["opponent_name"] = self._get_name(self._get_opponent_id(agent_id))
            response["last_opponent_action"] = self._last_actions.get(self._get_opponent_id(agent_id))
        
        return response

    def _get_opponent_id(self, my_id):
        for aid in self._turn_order:
            if aid != my_id: return aid
        return None

    def take_action(self, agent_id: int, action_name: str, params: dict = {}) -> None:
        if self._game_over or self._current_turn_id != agent_id:
            return

        agent_name = self._get_name(agent_id)

        # Irse al mazo está permitido siempre
        if action_name == "irse_al_mazo":
            self._last_log = f"{agent_name} se fue al mazo"
            self._handle_irse_al_mazo(agent_id)
            return

        if self._waiting_response:
            if action_name == "quiero":
                self._last_log = f"{agent_name} dijo: ¡QUIERO!"
                self._waiting_response = False
                
                if len(self._table_cards) == 1:
                    played_id = self._table_cards[0][0]
                    self._current_turn_id = self._get_opponent_id(played_id)
                else:
                    if len(self._round_history) > 0 and self._round_history[-1] is not None:
                        self._current_turn_id = self._round_history[-1]
                    else:
                        self._current_turn_id = self._mano_player_id

            elif action_name == "no_quiero":
                self._last_log = f"{agent_name} dijo: NO QUIERO"
                self._handle_no_quiero(agent_id)
                return
            
            elif action_name in ["retruco", "vale4"]:
                self._last_log = f"{agent_name} cantó: ¡{action_name.upper()}!"
                self._handle_bet_raise(agent_id, action_name)

        else:
            if action_name == "play_card":
                self._play_card(agent_id, params.get("index"))
            
            elif action_name == "truco":
                self._last_log = f"{agent_name} cantó: ¡TRUCO!"
                if self._bet_level == 1:
                    self._handle_bet_raise(agent_id, "truco")

        self._update_all_buffers()

    def _handle_bet_raise(self, agent_id, bet_type):
        if bet_type == "truco": self._bet_level = 2
        elif bet_type == "retruco": self._bet_level = 3
        elif bet_type == "vale4": self._bet_level = 4
        
        self._bet_caller_id = agent_id
        self._waiting_response = True
        self._current_turn_id = self._get_opponent_id(agent_id)

    def _handle_irse_al_mazo(self, quitter_id):
        winner_id = self._get_opponent_id(quitter_id)
        points = self._bet_level if not self._waiting_response else (self._bet_level - 1 if self._bet_level > 2 else 1)
        if self._waiting_response and self._bet_level == 2: points = 1
        
        self._scores[winner_id] += points
        winner_name = self._get_name(winner_id)
        quitter_name = self._get_name(quitter_id)
        print(f"\n{'*'*60}")
        print(f" {quitter_name} se fue al mazo")
        print(f" Gana la mano: {winner_name} (+{points} punto{'s' if points > 1 else ''})")
        print(f"{'*'*60}\n")
        self._start_new_hand()

    def _handle_no_quiero(self, refuser_id):
        winner_id = self._get_opponent_id(refuser_id)
        points = 1
        if self._bet_level == 3: points = 2
        elif self._bet_level == 4: points = 3
        
        self._scores[winner_id] += points
        winner_name = self._get_name(winner_id)
        refuser_name = self._get_name(refuser_id)
        print(f"\n{'*'*60}")
        print(f" {refuser_name} dijo NO QUIERO")
        print(f" Gana la mano: {winner_name} (+{points} punto{'s' if points > 1 else ''})")
        print(f"{'*'*60}\n")
        self._start_new_hand()

    def _play_card(self, agent_id, card_index):
        hand = self._hands[agent_id]
        if 0 <= card_index < len(hand):
            card = hand.pop(card_index)
            self._table_cards.append((agent_id, card))
            
            agent_name = self._get_name(agent_id)
            self._last_log = f"{agent_name} jugó: {card}"
            
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
            points = self._bet_level
            self._scores[hand_winner] += points
            winner_name = self._get_name(hand_winner)
            print(f"\n{'*'*60}")
            print(f" Gana la mano: {winner_name} (+{points} punto{'s' if points > 1 else ''})")
            print(f"{'*'*60}\n")
            self._start_new_hand()
        else:
            self._current_round_number += 1
            if winner_id is not None:
                self._current_turn_id = winner_id
            else:
                self._current_turn_id = self._mano_player_id

    def _check_hand_winner(self):
        history = self._round_history
        if len(history) < 2: return None

        r1 = history[0]
        r2 = history[1] if len(history) > 1 else None
        
        if r1 is not None and r1 == r2: return r1
        if r1 is not None and r2 is None: return r1
        if r1 is None and r2 is not None: return r2
        
        if len(history) == 3:
            r3 = history[2]
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

        table_named = [{"agent": self._get_name(pid), "card": str(c)} for pid, c in self._table_cards]
        mano_name = self._get_name(self._mano_player_id)
        current_turn_name = self._get_name(self._current_turn_id)

        match_winner_name = None
        if self._game_over:
            for aid, score in self._scores.items():
                if score >= 15:
                    match_winner_name = self._get_name(aid)
                    break

        for entry in self._statebuffers:
            agent_id = entry["agent_id"]
            buffer = entry["statebuffer"]
            
            # Calcular acciones legales para este agente
            legal_actions = []
            is_my_turn = (agent_id == self._current_turn_id) and not self._game_over
            
            if is_my_turn:
                if self._waiting_response:
                    legal_actions = ["quiero", "no_quiero"]
                    if self._bet_level == 2: legal_actions.append("retruco")
                    if self._bet_level == 3: legal_actions.append("vale4")
                else:
                    legal_actions.append("play_card")
                    if self._bet_level == 1: 
                        legal_actions.append("truco")
                
                legal_actions.append("irse_al_mazo")
            
            # Determinar bet_status
            bet_status = "Nada"
            if self._bet_level == 2:
                bet_status = "Truco"
            elif self._bet_level == 3:
                bet_status = "Retruco"
            elif self._bet_level == 4:
                bet_status = "Vale Cuatro"
            
            # Mensaje de estado
            status_msg = ""
            if self._waiting_response and self._current_turn_id == agent_id:
                status_msg = "Debes responder a la apuesta"
            
            # Última acción del oponente
            opponent_id = self._get_opponent_id(agent_id)
            last_opponent_action = self._last_actions.get(opponent_id)
            opponent_name = self._get_name(opponent_id)
            
            state = {
                "hand": [str(c) for c in self._hands.get(agent_id, [])],
                "table": table_named,
                "scores": scores_named,
                "mano_name": mano_name,
                "current_turn_name": current_turn_name,
                "round_history": history_named,
                "round_num": self._current_round_number,
                "match_winner_name": match_winner_name,
                "my_turn": is_my_turn,
                "game_over": self._game_over,
                "bet_status": bet_status,
                "status_msg": status_msg,
                "waiting_response": self._waiting_response,
                "last_opponent_action": last_opponent_action,
                "opponent_name": opponent_name,
                "legal_actions": legal_actions
            }
            buffer.update(state)