from renderers import IRenderer
import os

class TrucoConsoleRenderer(IRenderer):
    def __init__(self):
        self.buffer = None
        self._last_turn_id = None
        self._last_opponent_action = None
        self._env = None
        self._human_id = None
        self._last_state = None  # Guardar último estado
        self._last_rendered_turn = None  # Evitar renderizar múltiples veces el mismo turno
        self._waiting_for_input = False  # Flag para saber si estamos esperando input
        
    def observe(self, statebuffer):
        self.buffer = statebuffer
        self._human_id = statebuffer._agent_id if hasattr(statebuffer, '_agent_id') else None
    
    def set_environment(self, env):
        """Permite al renderer ejecutar acciones en el environment"""
        self._env = env
    
    def _print_opponent_action(self, opponent_name, action_data):
        """Imprime la acción que acaba de realizar el oponente"""
        action = action_data.get("action", "")
        params = action_data.get("params", {})
        
        if action == "play_card":
            card = params.get("card")
            if card:
                print(f"\n 🤖 [{opponent_name}] Jugó: {card[1]} de {card[0]}")
        elif action == "truco":
            print(f"\n 🤖 [{opponent_name}] Dice: ¡TRUCO!")
        elif action == "retruco":
            print(f"\n 🤖 [{opponent_name}] Dice: ¡RETRUCO!")
        elif action == "vale4":
            print(f"\n 🤖 [{opponent_name}] Dice: ¡VALE CUATRO!")
        elif action == "quiero":
            print(f"\n 🤖 [{opponent_name}] Dice: ¡QUIERO!")
        elif action == "no_quiero":
            print(f"\n 🤖 [{opponent_name}] Dice: ¡NO QUIERO!")
        elif action == "irse_al_mazo":
            print(f"\n 🤖 [{opponent_name}] SE VA AL MAZO")

    def render(self):
        # Si ya estamos esperando input, no renderizar de nuevo
        if self._waiting_for_input:
            return
            
        state = self.buffer.get_state()
        # Si no hay estado nuevo, usar el último guardado
        if not state:
            state = self._last_state
        else:
            self._last_state = state
            
        if not state:
            return
        
        # Evitar renderizar el mismo turno múltiples veces
        current_turn = (state.get('my_turn'), state.get('current_turn_name'))
        if current_turn == self._last_rendered_turn and not state.get('my_turn'):
            return
            
        self._last_rendered_turn = current_turn

        # Mostrar acción del oponente si es nueva
        last_opp_action = state.get("last_opponent_action")
        if last_opp_action and last_opp_action != self._last_opponent_action:
            self._last_opponent_action = last_opp_action
            self._print_opponent_action(state.get("opponent_name", "RIVAL"), last_opp_action)
        
        # Extraer datos del estado
        r_num = state.get("round_num", 1)
        scores = state.get("scores", {})
        my_turn = state.get("my_turn", False)
        table = state.get("table", [])
        mano_name = state.get("mano_name", "Desconocido")
        turn_name = state.get("current_turn_name", "...")
        hist = state.get("round_history", [])
        game_over = state.get("game_over", False)
        match_winner = state.get("match_winner_name", "Nadie")
        bet_status = state.get("bet_status", "Nada")
        status_msg = state.get("status_msg", "")

        # --- PANTALLA DE FIN DE JUEGO ---
        if game_over:
            print("\n" + "#"*64)
            print("#" + " "*62 + "#")
            winner_msg = f"¡FIN DEL PARTIDO! GANADOR: {match_winner}"
            padding = (62 - len(winner_msg)) // 2
            print("#" + " "*padding + winner_msg + " "*(62 - padding - len(winner_msg)) + "#")
            print("#" + " "*62 + "#")
            print("#"*64 + "\n")
            return

        # --- PANTALLA DE JUEGO ---
        ronda_str = ['Primera', 'Segunda', 'Tercera'][r_num-1] if r_num <= 3 else "Definición"
        score_items = [f"{name}: {pts}" for name, pts in scores.items()]
        score_str = "  |  ".join(score_items)

        print("\n" + "="*60)
        print(f" MARCADOR:  {score_str}")
        print(f" RONDA:     {ronda_str}   (Es Mano: {mano_name})") 
        print(f" APUESTA:   {bet_status}")
        print(f" HISTORIAL: {hist}")
        print("-" * 60)
        
        # Mostrar Cartas en Mesa
        if table:
            print(" MESA:")
            for play in table:
                print(f"   > {play['agent']} jugó: {play['card']}")
        else:
            print(" MESA: [ Vacía ]")
        
        print("-" * 60)

        # --- SECCIÓN DE ALERTAS Y TURNO ---
        if status_msg:
            print(f"\n [!] AVISO: {status_msg}")

        if my_turn:
            print("\n >>> ¡ES TU TURNO! <<<")
            print(" TUS CARTAS:")
            hand = state.get("hand", [])
            score_viz = " | ".join([f"{c}" for c in hand])
            print(f"   {score_viz}")
            
            # Solicitar input del usuario
            self._get_user_action(state)
        else:
            print(f"\n Esperando jugada de: {turn_name}...")
    
    def _get_user_action(self, state):
        """Solicita y ejecuta la acción del usuario"""
        legal_actions = state.get("legal_actions", [])
        hand = state.get("hand", [])
        
        print("\n" + "*"*30)
        print(" TU TURNO. Opciones:")
        
        options_map = {}
        idx_counter = 1
        
        # Listar opciones
        for action in legal_actions:
            if action == "play_card":
                for i, card in enumerate(hand):
                    print(f" {idx_counter}. Jugar {card}")
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
        
        # Obtener input
        self._waiting_for_input = True
        while True:
            try:
                user_input = input(">> Elige opción (número): ")
                choice = int(user_input)
                if choice in options_map:
                    action_name, params = options_map[choice]
                    # Ejecutar acción directamente en el environment
                    if self._env and self._human_id:
                        self._env.take_action(self._human_id, action_name, params)
                        self._waiting_for_input = False
                        self._last_rendered_turn = None  # Reset para permitir siguiente render
                    break
                else:
                    print("Opción inválida.")
            except ValueError:
                print("Ingresa un número.")
            except KeyboardInterrupt:
                self._waiting_for_input = False
                raise