import pygame
import sys
from typing import Optional
from renderers import Renderer
from trucoworld import Card, Suit


class PyGameTrucoRenderer(Renderer):
    def __init__(self, statebuffer, agent_id: int, human_agent=None):
        super(PyGameTrucoRenderer, self).__init__(statebuffer)
        self._agent_id = agent_id
        self._human_agent = human_agent
        
        pygame.init()
        self._width = 1200
        self._height = 800
        self._screen = pygame.display.set_mode((self._width, self._height))
        pygame.display.set_caption("Truco Argentino")
        
        self._font_large = pygame.font.Font(None, 48)
        self._font_medium = pygame.font.Font(None, 36)
        self._font_small = pygame.font.Font(None, 24)
        
        self._colors = {
            "background": (34, 139, 34),
            "card_bg": (255, 255, 255),
            "card_border": (0, 0, 0),
            "text": (255, 255, 255),
            "text_dark": (0, 0, 0),
            "highlight": (255, 215, 0),
            "button": (70, 130, 180),
            "button_hover": (100, 149, 237),
            "red": (220, 20, 60),
            "black": (0, 0, 0),
        }
        
        self._card_width = 80
        self._card_height = 120
        self._selected_card = None
        self._hovered_card = None
        self._hovered_button = None
        
        self._suit_symbols = {
            Suit.ESPADA: "♠",
            Suit.BASTO: "♣",
            Suit.ORO: "♦",
            Suit.COPA: "♥",
        }
        
        self._suit_colors = {
            Suit.ESPADA: self._colors["black"],
            Suit.BASTO: self._colors["black"],
            Suit.ORO: self._colors["red"],
            Suit.COPA: self._colors["red"],
        }
    
    def render(self):
        state = self._statebuffer.get()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if self._human_agent and state.get("current_player") == self._agent_id:
                self._handle_input(event, state)
        
        self._screen.fill(self._colors["background"])
        
        self._draw_scores(state)
        self._draw_played_cards(state)
        self._draw_player_hand(state)
        self._draw_game_info(state)
        self._draw_action_buttons(state)
        
        if state.get("game_over"):
            self._draw_game_over(state)
        
        pygame.display.flip()
    
    def _handle_input(self, event, state):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if self._hovered_card is not None:
                action = f"play_card_{self._hovered_card}"
                if action in state.get("valid_actions", []):
                    self._human_agent.set_action(action)
                    self._selected_card = None
            
            elif self._hovered_button:
                if self._hovered_button in state.get("valid_actions", []):
                    self._human_agent.set_action(self._hovered_button)
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover_state(pygame.mouse.get_pos(), state)
    
    def _update_hover_state(self, mouse_pos, state):
        self._hovered_card = None
        self._hovered_button = None
        
        hand = state.get("hand", [])
        hand_y = self._height - self._card_height - 40
        start_x = (self._width - len(hand) * (self._card_width + 10)) // 2
        
        for i in range(len(hand)):
            card_x = start_x + i * (self._card_width + 10)
            card_rect = pygame.Rect(card_x, hand_y, self._card_width, self._card_height)
            if card_rect.collidepoint(mouse_pos):
                self._hovered_card = i
                return
        
        button_actions = [a for a in state.get("valid_actions", []) if not a.startswith("play_card_")]
        button_y = self._height - 180
        button_width = 150
        button_height = 40
        start_x = (self._width - len(button_actions) * (button_width + 10)) // 2
        
        for i, action in enumerate(button_actions):
            button_x = start_x + i * (button_width + 10)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            if button_rect.collidepoint(mouse_pos):
                self._hovered_button = action
                return
    
    def _draw_card(self, surface, card: Card, x: int, y: int, highlight: bool = False):
        border_color = self._colors["highlight"] if highlight else self._colors["card_border"]
        border_width = 3 if highlight else 2
        
        pygame.draw.rect(surface, self._colors["card_bg"], (x, y, self._card_width, self._card_height))
        pygame.draw.rect(surface, border_color, (x, y, self._card_width, self._card_height), border_width)
        
        number_text = self._font_medium.render(str(card.number), True, self._suit_colors[card.suit])
        suit_text = self._font_large.render(self._suit_symbols[card.suit], True, self._suit_colors[card.suit])
        
        surface.blit(number_text, (x + 10, y + 10))
        surface.blit(suit_text, (x + self._card_width // 2 - suit_text.get_width() // 2, 
                                  y + self._card_height // 2 - suit_text.get_height() // 2))
    
    def _draw_card_back(self, surface, x: int, y: int):
        pygame.draw.rect(surface, (139, 69, 19), (x, y, self._card_width, self._card_height))
        pygame.draw.rect(surface, self._colors["card_border"], (x, y, self._card_width, self._card_height), 2)
        
        pattern_color = (160, 82, 45)
        for i in range(0, self._card_width, 10):
            pygame.draw.line(surface, pattern_color, (x + i, y), (x + i, y + self._card_height), 2)
        for i in range(0, self._card_height, 10):
            pygame.draw.line(surface, pattern_color, (x, y + i), (x + self._card_width, y + i), 2)
    
    def _draw_scores(self, state):
        scores = state.get("scores", {0: 0, 1: 0})
        
        score_text_0 = self._font_large.render(f"Jugador 1: {scores.get(0, 0)}", True, self._colors["text"])
        score_text_1 = self._font_large.render(f"Jugador 2: {scores.get(1, 0)}", True, self._colors["text"])
        
        self._screen.blit(score_text_0, (50, 30))
        self._screen.blit(score_text_1, (self._width - score_text_1.get_width() - 50, 30))
        
        current_player = state.get("current_player")
        if current_player == 0:
            pygame.draw.circle(self._screen, self._colors["highlight"], (30, 50), 10)
        elif current_player == 1:
            pygame.draw.circle(self._screen, self._colors["highlight"], 
                             (self._width - 30, 50), 10)
    
    def _draw_played_cards(self, state):
        played_cards = state.get("played_cards", {0: [], 1: []})
        
        player0_cards = played_cards.get(0, [])
        player1_cards = played_cards.get(1, [])
        
        center_y = self._height // 2 - self._card_height // 2
        
        for i, card in enumerate(player0_cards):
            x = self._width // 2 - self._card_width - 20 - i * 30
            self._draw_card(self._screen, card, x, center_y)
        
        for i, card in enumerate(player1_cards):
            x = self._width // 2 + 20 + i * 30
            self._draw_card(self._screen, card, x, center_y)
        
        round_winners = state.get("round_winners", [])
        if round_winners:
            winner_text = f"Rondas: "
            for i, winner in enumerate(round_winners):
                if winner == 0:
                    winner_text += "J1 "
                elif winner == 1:
                    winner_text += "J2 "
                else:
                    winner_text += "= "
            
            text_surface = self._font_small.render(winner_text, True, self._colors["text"])
            self._screen.blit(text_surface, (self._width // 2 - text_surface.get_width() // 2, 
                                            center_y - 40))
    
    def _draw_player_hand(self, state):
        if state.get("current_player") == self._agent_id:
            hand = state.get("hand", [])
        else:
            opponent_hand_size = state.get("opponent_hand_size", 0)
            hand = [None] * opponent_hand_size
        
        hand_y = self._height - self._card_height - 40
        start_x = (self._width - len(hand) * (self._card_width + 10)) // 2
        
        for i, card in enumerate(hand):
            card_x = start_x + i * (self._card_width + 10)
            
            if card is None:
                self._draw_card_back(self._screen, card_x, hand_y)
            else:
                highlight = (i == self._hovered_card and 
                           state.get("current_player") == self._agent_id)
                self._draw_card(self._screen, card, card_x, hand_y, highlight)
    
    def _draw_game_info(self, state):
        truco_state = state.get("truco_state", {})
        envido_state = state.get("envido_state", {})
        
        info_y = 100
        
        if truco_state.get("level", 0) > 0:
            truco_names = ["", "Truco", "Retruco", "Vale Cuatro"]
            truco_text = self._font_medium.render(
                f"{truco_names[truco_state['level']]} {'(Aceptado)' if truco_state.get('accepted') else '(Pendiente)'}",
                True, self._colors["text"]
            )
            self._screen.blit(truco_text, (self._width // 2 - truco_text.get_width() // 2, info_y))
            info_y += 40
        
        if envido_state.get("called"):
            envido_text = self._font_medium.render(
                f"Envido: {envido_state.get('type', '')}",
                True, self._colors["text"]
            )
            self._screen.blit(envido_text, (self._width // 2 - envido_text.get_width() // 2, info_y))
    
    def _draw_action_buttons(self, state):
        if state.get("current_player") != self._agent_id or not self._human_agent:
            return
        
        valid_actions = state.get("valid_actions", [])
        button_actions = [a for a in valid_actions if not a.startswith("play_card_")]
        
        if not button_actions:
            return
        
        button_width = 150
        button_height = 40
        button_y = self._height - 180
        start_x = (self._width - len(button_actions) * (button_width + 10)) // 2
        
        action_names = {
            "truco": "Truco",
            "retruco": "Retruco",
            "vale_cuatro": "Vale 4",
            "envido": "Envido",
            "real_envido": "Real Envido",
            "falta_envido": "Falta Envido",
            "accept_truco": "Quiero",
            "reject_truco": "No Quiero",
        }
        
        for i, action in enumerate(button_actions):
            button_x = start_x + i * (button_width + 10)
            
            is_hovered = (action == self._hovered_button)
            button_color = self._colors["button_hover"] if is_hovered else self._colors["button"]
            
            pygame.draw.rect(self._screen, button_color, 
                           (button_x, button_y, button_width, button_height))
            pygame.draw.rect(self._screen, self._colors["text"], 
                           (button_x, button_y, button_width, button_height), 2)
            
            button_text = self._font_small.render(action_names.get(action, action), 
                                                  True, self._colors["text"])
            text_x = button_x + button_width // 2 - button_text.get_width() // 2
            text_y = button_y + button_height // 2 - button_text.get_height() // 2
            self._screen.blit(button_text, (text_x, text_y))
    
    def _draw_game_over(self, state):
        overlay = pygame.Surface((self._width, self._height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self._screen.blit(overlay, (0, 0))
        
        scores = state.get("scores", {0: 0, 1: 0})
        winner = 0 if scores.get(0, 0) >= 15 else 1
        
        game_over_text = self._font_large.render("¡Juego Terminado!", True, self._colors["text"])
        winner_text = self._font_large.render(f"Ganador: Jugador {winner + 1}", True, self._colors["highlight"])
        score_text = self._font_medium.render(
            f"Puntaje Final: {scores.get(0, 0)} - {scores.get(1, 0)}", 
            True, self._colors["text"]
        )
        
        self._screen.blit(game_over_text, 
                         (self._width // 2 - game_over_text.get_width() // 2, self._height // 2 - 100))
        self._screen.blit(winner_text, 
                         (self._width // 2 - winner_text.get_width() // 2, self._height // 2 - 30))
        self._screen.blit(score_text, 
                         (self._width // 2 - score_text.get_width() // 2, self._height // 2 + 40))
