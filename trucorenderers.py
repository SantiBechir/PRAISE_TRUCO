from renderers import IRenderer
import os

class TrucoConsoleRenderer(IRenderer):
    def __init__(self):
        self.buffer = None
        self._last_turn_id = None
        
    def observe(self, statebuffer):
        self.buffer = statebuffer

    """def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')"""

    def render(self):
        state = self.buffer.get_state()
        if state:
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
            print(f" APUESTA:   {bet_status}")  # <--- Nuevo indicador
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
                # Las cartas y opciones las muestra el Agente Manual en su input,
                # pero aquí podemos mostrar la mano actual como referencia visual.
                print(" TUS CARTAS:")
                hand = state.get("hand", [])
                score_viz = " | ".join([f"{c}" for c in hand])
                print(f"   {score_viz}")
            else:
                print(f"\n Esperando jugada de: {turn_name}...")