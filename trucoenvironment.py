import random
from environments import SimulatedEnvironment

# Valores de las cartas (Jerarquía)
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
        
        # Niveles: 1 (nada), 2 (Truco), 3 (Retruco), 4 (Vale 4)
        self._bet_level = 1 
        self._bet_caller_id = None # Quién cantó último
        self._waiting_response = False # Si estamos esperando un Quiero/No Quiero
        self._current_turn_id = None # Quién tiene la acción ahora
        
        self._agent_names = {}

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
        
        # Reset de apuestas
        self._bet_level = 1
        self._waiting_response = False
        self._bet_caller_id = None
        
        for agent_id in self._turn_order:
            self._hands[agent_id] = [self._deck.pop() for _ in range(3)]
        
        self._current_turn_id = self._mano_player_id
        self._update_all_buffers()

    def get_property(self, agent_id: int, property_name: str) -> dict:
        if agent_id not in self._agents:
            return {}
        
        response = {"agent": agent_id}
        
        # Sensores básicos
        if property_name == "hand":
            response["hand"] = [(c.number, c.suit) for c in self._hands[agent_id]]
        elif property_name == "table":
            response["table"] = [{"agent": self._get_name(aid), "card": str(c)} for aid, c in self._table_cards]
        
        # Sensor de Estado de Juego (Turno y Apuestas)
        elif property_name == "game_state":
            # Calculamos acciones legales para este agente
            legal_actions = []
            
            is_my_turn = (agent_id == self._current_turn_id) and not self._game_over
            
            if is_my_turn:
                if self._waiting_response:
                    # Si me toca y están esperando respuesta, SOLO puedo responder
                    legal_actions = ["quiero", "no_quiero"]
                    # Solo puedo subir la apuesta si no es Vale 4
                    if self._bet_level == 2: legal_actions.append("retruco")
                    if self._bet_level == 3: legal_actions.append("vale4")
                else:
                    # Turno normal: puedo jugar carta o cantar si no canté yo recién
                    legal_actions.append("play_card")
                    # Lógica simple: si nadie cantó, puedo cantar Truco
                    if self._bet_level == 1: 
                        legal_actions.append("truco")
                    # Si el otro cantó y yo quise, yo no puedo retrucar inmediatamente en el mismo turno
                # Siempre puedo irme al mazo (abandonar la mano)
                legal_actions.append("irse_al_mazo")
            
            response["is_my_turn"] = is_my_turn
            response["waiting_response"] = self._waiting_response
            response["current_bet_level"] = self._bet_level
            response["legal_actions"] = legal_actions
            response["opponent_name"] = self._get_name(self._get_opponent_id(agent_id))

        return response

    def _get_opponent_id(self, my_id):
        for aid in self._turn_order:
            if aid != my_id: return aid
        return None

    def take_action(self, agent_id: int, action_name: str, params: dict = {}) -> None:
        if self._game_over or self._current_turn_id != agent_id:
            return

        # --- MANEJO DE ACCIONES ---
        
        if self._waiting_response:
            # Estamos en fase de respuesta a un canto
            if action_name == "quiero":
                self._waiting_response = False
                # Después de aceptar, el turno debe volver a jugar cartas
                # Si hay alguien que ya jugó carta en la mesa y el otro no, 
                # el turno es del que NO jugó
                if len(self._table_cards) == 1:
                    # Ya hay una carta jugada, el turno es del que no jugó
                    played_id = self._table_cards[0][0]
                    self._current_turn_id = self._get_opponent_id(played_id)
                else:
                    # No hay cartas jugadas, el turno vuelve al que debe empezar esta ronda
                    # (quien ganó la anterior, o mano si es primera)
                    if len(self._round_history) > 0 and self._round_history[-1] is not None:
                        self._current_turn_id = self._round_history[-1]
                    else:
                        self._current_turn_id = self._mano_player_id
                
            elif action_name == "no_quiero":
                self._handle_no_quiero(agent_id)
                return # Terminó la mano
            
            elif action_name == "irse_al_mazo":
                self._handle_irse_al_mazo(agent_id)
                return # Terminó la mano
                
            elif action_name in ["retruco", "vale4"]:
                self._handle_bet_raise(agent_id, action_name)
                
        else:
            # Fase normal de juego
            if action_name == "play_card":
                self._play_card(agent_id, params.get("index"))
            
            elif action_name == "irse_al_mazo":
                self._handle_irse_al_mazo(agent_id)
                return # Terminó la mano
            
            elif action_name == "truco":
                if self._bet_level == 1:
                    self._handle_bet_raise(agent_id, "truco")

        self._update_all_buffers()

    def _handle_bet_raise(self, agent_id, bet_type):
        """Maneja la subida de apuesta y cambio de turno para responder"""
        if bet_type == "truco": self._bet_level = 2
        elif bet_type == "retruco": self._bet_level = 3
        elif bet_type == "vale4": self._bet_level = 4
        
        self._bet_caller_id = agent_id
        self._waiting_response = True
        # Pasamos el turno al oponente para que responda
        self._current_turn_id = self._get_opponent_id(agent_id)

    def _handle_irse_al_mazo(self, quitter_id):
        """Alguien se fue al mazo. El otro gana los puntos según el contexto."""
        winner_id = self._get_opponent_id(quitter_id)
        
        # Si hay una apuesta pendiente de respuesta, irse al mazo = rechazar el canto
        # Da los puntos ANTERIORES al canto (igual que NO_QUIERO)
        if self._waiting_response:
            points = 1
            if self._bet_level == 2: points = 1
            elif self._bet_level == 3: points = 2
            elif self._bet_level == 4: points = 3
        else:
            # Si no hay apuesta pendiente, se fue al mazo voluntariamente
            # Da los puntos del nivel actual de apuesta
            points = self._bet_level
        
        self._scores[winner_id] += points
        
        # Mensaje de ganador por abandono
        winner_name = self._agent_names.get(winner_id, "Desconocido")
        quitter_name = self._agent_names.get(quitter_id, "Desconocido")
        print("\n" + "="*60)
        print(f"🏆 ¡{quitter_name} SE FUE AL MAZO!")
        print(f"   Mano ganada por {winner_name} (+{points} punto{'s' if points > 1 else ''})")
        p1_id, p2_id = self._turn_order[0], self._turn_order[1]
        print(f"   Marcador: {self._agent_names.get(p1_id, 'J1')} {self._scores[p1_id]} - {self._scores[p2_id]} {self._agent_names.get(p2_id, 'J2')}")
        print("="*60 + "\n")
        
        self._start_new_hand()
    
    def _handle_no_quiero(self, refuser_id):
        """Alguien dijo no quiero. El otro gana los puntos ANTERIORES al canto."""
        winner_id = self._get_opponent_id(refuser_id)
        
        # Puntos a otorgar: Si era Truco (2), el rechazo da 1.
        # Si era Retruco (3), el rechazo da 2. Si Vale4 (4), rechazo da 3.
        points = 1
        if self._bet_level == 2: points = 1
        elif self._bet_level == 3: points = 2
        elif self._bet_level == 4: points = 3
        
        self._scores[winner_id] += points
        
        # Mensaje de ganador por rechazo
        winner_name = self._agent_names.get(winner_id, "Desconocido")
        refuser_name = self._agent_names.get(refuser_id, "Desconocido")
        print("\n" + "="*60)
        print(f"🏆 ¡{refuser_name} SE FUE AL MAZO!")
        print(f"   Mano ganada por {winner_name} (+{points} punto{'s' if points > 1 else ''})")
        p1_id, p2_id = self._turn_order[0], self._turn_order[1]
        print(f"   Marcador: {self._agent_names.get(p1_id, 'J1')} {self._scores[p1_id]} - {self._scores[p2_id]} {self._agent_names.get(p2_id, 'J2')}")
        print("="*60 + "\n")
        
        self._start_new_hand()

    def _play_card(self, agent_id, card_index):
        hand = self._hands[agent_id]
        if card_index is not None and 0 <= card_index < len(hand):
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
            # Puntos según el nivel de apuesta querido
            points = self._bet_level
            self._scores[hand_winner] += points
            
            # Mensaje de ganador de la mano
            winner_name = self._agent_names.get(hand_winner, "Desconocido")
            print("\n" + "="*60)
            print(f"🏆 ¡MANO GANADA POR {winner_name}! (+{points} punto{'s' if points > 1 else ''})")
            p1_id, p2_id = self._turn_order[0], self._turn_order[1]
            print(f"   Marcador: {self._agent_names.get(p1_id, 'J1')} {self._scores[p1_id]} - {self._scores[p2_id]} {self._agent_names.get(p2_id, 'J2')}")
            print("="*60 + "\n")
            
            self._start_new_hand()
        else:
            self._current_round_number += 1
            if winner_id is not None:
                self._current_turn_id = winner_id
            else:
                self._current_turn_id = self._mano_player_id

    def _check_hand_winner(self):
        history = self._round_history
        
        # Caso: Gana directo con 2 victorias
        if len(history) >= 2:
            r1, r2 = history[0], history[1]
            # Si ganó las 2 primeras
            if r1 is not None and r1 == r2:
                return r1
        
        # Caso: Primera ganada + Segunda parda = gana el de la primera
        if len(history) >= 2:
            r1, r2 = history[0], history[1]
            if r1 is not None and r2 is None:
                return r1
        
        # Caso: Primera parda + Segunda ganada = gana el de la segunda
        if len(history) >= 2:
            r1, r2 = history[0], history[1]
            if r1 is None and r2 is not None:
                return r2
        
        # Caso: Llegamos a la tercera ronda
        if len(history) == 3:
            r1, r2, r3 = history[0], history[1], history[2]
            
            # Si alguien ganó 2 de 3
            wins = {}
            for res in history:
                if res is not None:
                    wins[res] = wins.get(res, 0) + 1
            
            for pid, count in wins.items():
                if count >= 2:
                    return pid
            
            # Si todas pardas o no hay ganador claro, gana el mano
            if r1 is None and r2 is None and r3 is None:
                return self._mano_player_id
        
        return None

    def _update_all_buffers(self):
        scores_named = {self._get_name(aid): score for aid, score in self._scores.items()}
        
        history_named = []
        nombres_rondas = ["1ra", "2da", "3ra"]
        for i, res in enumerate(self._round_history):
            ganador = self._get_name(res) if res is not None else "Parda"
            history_named.append(f"{nombres_rondas[i]}:{ganador}")

        # --- CORRECCIÓN AQUÍ ---
        # Enviamos un diccionario, no un string formateado
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
            
            state = {
                "hand": [str(c) for c in self._hands.get(agent_id, [])],
                "table": table_named, # Ahora es una lista de dicts compatible con el renderer
                "scores": scores_named,
                "mano_name": mano_name,
                "current_turn_name": current_turn_name,
                "round_history": history_named,
                "round_num": self._current_round_number,
                "match_winner_name": match_winner_name,
                "my_turn": (self._current_turn_id == agent_id) and not self._game_over,
                "game_over": self._game_over
            }
            buffer.update(state)