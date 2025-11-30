import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from statebuffer import IStateBuffer
from environments import SimulatedEnvironment


class Suit(Enum):
    ESPADA = "espada"
    BASTO = "basto"
    ORO = "oro"
    COPA = "copa"


class Card:
    def __init__(self, number: int, suit: Suit):
        self.number = number
        self.suit = suit
        self.power = self._calculate_power()
    
    def _calculate_power(self) -> int:
        hierarchy = {
            (1, Suit.ESPADA): 14,
            (1, Suit.BASTO): 13,
            (7, Suit.ESPADA): 12,
            (7, Suit.ORO): 11,
            (3, Suit.ESPADA): 10, (3, Suit.BASTO): 10, (3, Suit.ORO): 10, (3, Suit.COPA): 10,
            (2, Suit.ESPADA): 9, (2, Suit.BASTO): 9, (2, Suit.ORO): 9, (2, Suit.COPA): 9,
            (1, Suit.ORO): 8, (1, Suit.COPA): 8,
            (12, Suit.ESPADA): 7, (12, Suit.BASTO): 7, (12, Suit.ORO): 7, (12, Suit.COPA): 7,
            (11, Suit.ESPADA): 6, (11, Suit.BASTO): 6, (11, Suit.ORO): 6, (11, Suit.COPA): 6,
            (10, Suit.ESPADA): 5, (10, Suit.BASTO): 5, (10, Suit.ORO): 5, (10, Suit.COPA): 5,
            (7, Suit.BASTO): 4, (7, Suit.COPA): 4,
            (6, Suit.ESPADA): 3, (6, Suit.BASTO): 3, (6, Suit.ORO): 3, (6, Suit.COPA): 3,
            (5, Suit.ESPADA): 2, (5, Suit.BASTO): 2, (5, Suit.ORO): 2, (5, Suit.COPA): 2,
            (4, Suit.ESPADA): 1, (4, Suit.BASTO): 1, (4, Suit.ORO): 1, (4, Suit.COPA): 1,
        }
        return hierarchy.get((self.number, self.suit), 0)
    
    def __repr__(self):
        return f"{self.number} de {self.suit.value}"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.number == other.number and self.suit == other.suit


class TrucoEnvironment(SimulatedEnvironment):
    def __init__(self):
        super(TrucoEnvironment, self).__init__()
        self._deck = []
        self._player_hands = {}
        self._played_cards = {0: [], 1: []}
        self._round_winners = []
        self._scores = {0: 0, 1: 0}
        self._current_player = 0
        self._hand_starter = 0
        self._round_number = 0
        self._game_over = False
        self._envido_state = {"called": False, "accepted": False, "points": 0}
        self._truco_state = {"level": 0, "called_by": None, "accepted": False}
        self._initialize_deck()
        
    def _initialize_deck(self):
        self._deck = []
        for suit in Suit:
            for number in [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]:
                self._deck.append(Card(number, suit))
    
    def add(self, agent_id: int) -> None:
        if len(self._agents) >= 2:
            raise ValueError("Solo se permiten 2 jugadores")
        super(TrucoEnvironment, self).add(agent_id)
        self._player_hands[agent_id] = []
        
    def add_statebuffer(self, agent_id: int, statebuffer: IStateBuffer) -> None:
        super(TrucoEnvironment, self).add_statebuffer(agent_id, statebuffer)
        self._update_statebuffer(agent_id, statebuffer)
    
    def _update_statebuffer(self, agent_id: int, statebuffer: IStateBuffer):
        opponent_id = 1 - agent_id if agent_id in [0, 1] else None
        statebuffer.update({
            "hand": self._player_hands.get(agent_id, []),
            "played_cards": self._played_cards,
            "round_winners": self._round_winners,
            "scores": self._scores,
            "current_player": self._current_player,
            "round_number": self._round_number,
            "game_over": self._game_over,
            "envido_state": self._envido_state,
            "truco_state": self._truco_state,
            "opponent_hand_size": len(self._player_hands.get(opponent_id, [])),
        })
    
    def _update_all_statebuffers(self):
        for entry in self._statebuffers:
            self._update_statebuffer(entry["agent_id"], entry["statebuffer"])
    
    def deal_cards(self):
        random.shuffle(self._deck)
        self._player_hands = {agent_id: [] for agent_id in self._agents}
        for i, agent_id in enumerate(self._agents):
            self._player_hands[agent_id] = self._deck[i*3:(i+1)*3]
        self._played_cards = {0: [], 1: []}
        self._round_winners = []
        self._round_number = 0
        self._envido_state = {"called": False, "accepted": False, "points": 0}
        self._truco_state = {"level": 0, "called_by": None, "accepted": False}
        self._update_all_statebuffers()
    
    def get_property(self, agent_id: int, property_name: str) -> dict:
        if agent_id not in self._agents:
            return {}
        
        response = {"agent": agent_id}
        property_methods = {
            "hand": lambda aid: self._player_hands.get(aid, []),
            "played_cards": lambda aid: self._played_cards,
            "current_player": lambda aid: self._current_player,
            "scores": lambda aid: self._scores,
            "round_winners": lambda aid: self._round_winners,
            "game_over": lambda aid: self._game_over,
            "valid_actions": lambda aid: self._get_valid_actions(aid),
        }
        
        property_method = property_methods.get(property_name)
        if property_method:
            response[property_name] = property_method(agent_id)
        
        return response
    
    def _get_valid_actions(self, agent_id: int) -> List[str]:
        if self._game_over or self._current_player != agent_id:
            return []
        
        actions = []
        if self._player_hands.get(agent_id):
            actions.extend([f"play_card_{i}" for i in range(len(self._player_hands[agent_id]))])
        
        if not self._envido_state["called"] and self._round_number == 0:
            actions.extend(["envido", "real_envido", "falta_envido"])
        
        if self._truco_state["level"] == 0:
            actions.append("truco")
        elif self._truco_state["level"] == 1 and self._truco_state["called_by"] != agent_id:
            actions.extend(["retruco", "accept_truco", "reject_truco"])
        elif self._truco_state["level"] == 2 and self._truco_state["called_by"] != agent_id:
            actions.extend(["vale_cuatro", "accept_truco", "reject_truco"])
        
        return actions
    
    def take_action(self, agent_id: int, action_name: str, params: dict = {}) -> None:
        if agent_id not in self._agents or self._game_over:
            return
        
        if action_name.startswith("play_card_"):
            card_index = int(action_name.split("_")[-1])
            self._play_card(agent_id, card_index)
        elif action_name in ["envido", "real_envido", "falta_envido"]:
            self._handle_envido(agent_id, action_name)
        elif action_name == "truco":
            self._handle_truco(agent_id)
        elif action_name == "retruco":
            self._handle_retruco(agent_id)
        elif action_name == "vale_cuatro":
            self._handle_vale_cuatro(agent_id)
        elif action_name == "accept_truco":
            self._accept_truco(agent_id)
        elif action_name == "reject_truco":
            self._reject_truco(agent_id)
        
        self._update_all_statebuffers()
    
    def _play_card(self, agent_id: int, card_index: int):
        if card_index >= len(self._player_hands[agent_id]):
            return
        
        card = self._player_hands[agent_id].pop(card_index)
        self._played_cards[agent_id].append(card)
        
        opponent_id = 1 - agent_id
        if len(self._played_cards[opponent_id]) == len(self._played_cards[agent_id]):
            self._resolve_round()
        else:
            self._current_player = opponent_id
    
    def _resolve_round(self):
        player0_card = self._played_cards[0][-1] if self._played_cards[0] else None
        player1_card = self._played_cards[1][-1] if self._played_cards[1] else None
        
        if player0_card and player1_card:
            if player0_card.power > player1_card.power:
                self._round_winners.append(0)
                self._current_player = 0
            elif player1_card.power > player0_card.power:
                self._round_winners.append(1)
                self._current_player = 1
            else:
                self._round_winners.append(-1)
                self._current_player = self._hand_starter
        
        self._round_number += 1
        
        if self._is_hand_over():
            self._resolve_hand()
    
    def _is_hand_over(self) -> bool:
        if len(self._round_winners) < 2:
            return False
        
        player0_wins = self._round_winners.count(0)
        player1_wins = self._round_winners.count(1)
        
        return player0_wins >= 2 or player1_wins >= 2 or len(self._round_winners) >= 3
    
    def _resolve_hand(self):
        player0_wins = self._round_winners.count(0)
        player1_wins = self._round_winners.count(1)
        
        points = 1
        if self._truco_state["accepted"]:
            points = [2, 3, 4][self._truco_state["level"]]
        
        if player0_wins > player1_wins:
            self._scores[0] += points
        elif player1_wins > player0_wins:
            self._scores[1] += points
        else:
            self._scores[self._hand_starter] += points
        
        if self._scores[0] >= 15 or self._scores[1] >= 15:
            self._game_over = True
        else:
            self._hand_starter = 1 - self._hand_starter
            self._current_player = self._hand_starter
            self.deal_cards()
    
    def _handle_envido(self, agent_id: int, envido_type: str):
        self._envido_state["called"] = True
        self._envido_state["type"] = envido_type
    
    def _handle_truco(self, agent_id: int):
        self._truco_state["level"] = 1
        self._truco_state["called_by"] = agent_id
        self._current_player = 1 - agent_id
    
    def _handle_retruco(self, agent_id: int):
        self._truco_state["level"] = 2
        self._truco_state["called_by"] = agent_id
        self._current_player = 1 - agent_id
    
    def _handle_vale_cuatro(self, agent_id: int):
        self._truco_state["level"] = 3
        self._truco_state["called_by"] = agent_id
        self._current_player = 1 - agent_id
    
    def _accept_truco(self, agent_id: int):
        self._truco_state["accepted"] = True
        self._current_player = agent_id
    
    def _reject_truco(self, agent_id: int):
        opponent_id = 1 - agent_id
        self._scores[opponent_id] += [1, 2, 3][self._truco_state["level"] - 1]
        
        if self._scores[opponent_id] >= 15:
            self._game_over = True
        else:
            self._hand_starter = 1 - self._hand_starter
            self._current_player = self._hand_starter
            self.deal_cards()
