import threading
import time
import sys
from statebuffer import StateBuffer
from trucoenvironment import TrucoEnvironment
from trucoagents import ManualTrucoAgent, RandomTrucoAgent
from trucorenderers import TrucoConsoleRenderer

def agent_thread(agent, env):
    while not env.game_over:
        agent.behave()
        time.sleep(0.5)

def render_thread(renderer, env):
    while not env.game_over:
        renderer.render()
        time.sleep(0.5)
    # Un ultimo render para mostrar la pantalla de Game Over
    renderer.render()

if __name__ == '__main__':
    print("Iniciando Truco PRAISE...")
    
    #Crear Entorno
    env = TrucoEnvironment()

    # Crear Agentes
    human_agent = ManualTrucoAgent(env)
    bot_agent = RandomTrucoAgent(env)

    # Configurar Nombres
    env.set_agent_name(human_agent.id, "YO (Humano)")
    env.set_agent_name(bot_agent.id, "RIVAL (Bot)")

    # Configurar Renderer
    renderer = TrucoConsoleRenderer()
    human_buffer = StateBuffer(human_agent.id, env)
    renderer.observe(statebuffer=human_buffer)

    # Crear Hilos (Pasando env para controlar el cierre)
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

    # Bucle principal de control
    try:
        while not env.game_over:
            time.sleep(1)
        sys.exit(0)

    except KeyboardInterrupt:
        print("Salida forzada por usuario.")