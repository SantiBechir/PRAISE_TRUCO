import time
import sys
from statebuffer import StateBuffer
from trucoenvironment import TrucoEnvironment
from trucoagents import ManualTrucoAgent, RandomTrucoAgent
from trucorenderers import TrucoConsoleRenderer

if __name__ == '__main__':
    # Crear Entorno
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
    env._update_all_buffers()
    renderer.observe(statebuffer=human_buffer)
    renderer.set_environment(env)

    # Bucle principal
    try:
        while not env.game_over:
            # Bot juega si es su turno
            bot_agent.behave()
            
            # Renderizar y permitir input del humano
            renderer.render()
            
            time.sleep(0.1)
        
        # Render final
        renderer.render()
        print("\n🎮 Partida finalizada.")
        
    except KeyboardInterrupt:
        print("\n\nSalida forzada por usuario.")