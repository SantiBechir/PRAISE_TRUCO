from renderers import IRenderer

class TrucoConsoleRenderer(IRenderer):
    def __init__(self):
        self.buffer = None
        
    def observe(self, statebuffer):
        self.buffer = statebuffer

    def render(self):
        state = self.buffer.get_state()
        if state:
            r_num = state.get("round_num", 1)
            scores = state.get("scores", {})
            my_turn = state.get("my_turn", False)
            table = state.get("table", [])
            mano_name = state.get("mano_name", "Desconocido")
            turn_name = state.get("current_turn_name", "...")
            hist = state.get("round_history", [])
            game_over = state.get("game_over", False)
            match_winner = state.get("match_winner_name", "Nadie")
            
            # --- PANTALLA DE FIN DE JUEGO ---
            if game_over:
                print("\n" + "#"*64)
                print("#" + " "*62 + "#")
                winner_msg = f"¡FIN DEL PARTIDO! GANADOR: {match_winner}"
                padding = (62 - len(winner_msg)) // 2
                print("#" + " "*padding + winner_msg + " "*(62 - padding - len(winner_msg)) + "#")
                print("#" + " "*62 + "#")
                print("#"*64 + "\n")
                return # Salimos del render para no dibujar nada más

            # --- PANTALLA DE JUEGO ---
            ronda_str = ['Primera', 'Segunda', 'Tercera'][r_num-1]
            score_items = [f"{name}: {pts}" for name, pts in scores.items()]
            score_str = "  |  ".join(score_items)

            print("\n" + "="*60)
            print(f" MARCADOR:  {score_str}")
            print(f" RONDA:     {ronda_str}   (Es Mano: {mano_name})") 
            print(f" HISTORIAL: {hist}") # <--- Cambio solicitado: BAZAS -> HISTORIAL
            print("-" * 60)
            
            if table:
                print(f" MESA: {table}")
            else:
                print(" MESA: [ ... ]")
            
            if my_turn:
                print("\n >>> ¡TE TOCA! <<<")
                print(" TUS CARTAS:")
                hand = state.get("hand", [])
                for i, c in enumerate(hand):
                    print(f"   Opción [{i}]: {c}")
            else:
                # <--- Mensaje mejorado: Muestra exactamente a quién esperamos
                print(f"\n Esperando jugada de: {turn_name}...")