import threading
import time
import sys
from statebuffer import StateBuffer
from trucoenvironment import TrucoEnvironment
from trucoagents import ManualTrucoAgent, RandomTrucoAgent
from trucorenderers import TrucoConsoleRenderer

def agent_thread(agent, env):
    """El hilo del agente corre mientras el juego no haya terminado"""
    while not env.game_over:
        agent.behave()
        time.sleep(0.5)

def render_thread(renderer, env):
    """El render corre mientras no termine el juego"""
    while not env.game_over:
        renderer.render()
        time.sleep(0.5)
    # Un ultimo render para mostrar la pantalla de Game Over
    renderer.render()

if __name__ == '__main__':
    print("Iniciando Truco PRAISE...")
    
    # 1. Crear Entorno
    env = TrucoEnvironment()

    # 2. Crear Agentes
    human_agent = ManualTrucoAgent(env)
    bot_agent = RandomTrucoAgent(env)

    # Configurar Nombres
    env.set_agent_name(human_agent.id, "YO (Humano)")
    env.set_agent_name(bot_agent.id, "RIVAL (Bot)")

    # 3. Configurar Renderer
    renderer = TrucoConsoleRenderer()
    human_buffer = StateBuffer(human_agent.id, env)
    renderer.observe(statebuffer=human_buffer)

    # 4. Crear Hilos (Pasando env para controlar el cierre)
    thread_human = threading.Thread(target=agent_thread, args=(human_agent, env))
    thread_bot = threading.Thread(target=agent_thread, args=(bot_agent, env))
    thread_renderer = threading.Thread(target=render_thread, args=(renderer, env))

    # Daemon threads para asegurar que mueran si el main muere
    thread_renderer.daemon = True
    thread_human.daemon = True 
    thread_bot.daemon = True

    thread_renderer.start()
    thread_human.start()
    thread_bot.start()

    # 5. Bucle principal de control
    try:
        while not env.game_over:
            time.sleep(1)
        
        # Juego terminado detectado
        print("\nCerrando juego en 3 segundos...")
        time.sleep(3) # Dar tiempo para leer el cartel de ganador
        sys.exit(0)

    except KeyboardInterrupt:
        print("Salida forzada por usuario.")