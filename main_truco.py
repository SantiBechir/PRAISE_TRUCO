import time
import threading
from statebuffer import StateBuffer
from trucoworld import TrucoEnvironment
from trucoagent import HumanTrucoAgent, RandomTrucoAgent, TrucoSensor, TrucoActuator
from trucorenderers import PyGameTrucoRenderer


def agent_thread(agent, event_agent, event_renderer, timeout=0.1):
    while True:
        event_agent.wait(timeout=timeout)
        event_agent.clear()
        
        agent.behave()
        
        event_renderer.set()
        time.sleep(0.05)


def renderer_thread(renderer, event_agent, event_renderer, timeout=0.1):
    while True:
        event_renderer.wait(timeout=timeout)
        event_renderer.clear()
        
        renderer.render()
        
        event_agent.set()


def main():
    env = TrucoEnvironment()
    
    human_agent = HumanTrucoAgent()
    random_agent = RandomTrucoAgent()
    
    sensor_human = TrucoSensor(env)
    actuator_human = TrucoActuator(env)
    sensor_human.agent = human_agent
    actuator_human.agent = human_agent
    human_agent.add_sensor("sensor", sensor_human)
    human_agent.add_actuator("actuator", actuator_human)
    
    sensor_random = TrucoSensor(env)
    actuator_random = TrucoActuator(env)
    sensor_random.agent = random_agent
    actuator_random.agent = random_agent
    random_agent.add_sensor("sensor", sensor_random)
    random_agent.add_actuator("actuator", actuator_random)
    
    statebuffer_human = StateBuffer()
    statebuffer_random = StateBuffer()
    
    env.add_statebuffer(human_agent.id, statebuffer_human)
    env.add_statebuffer(random_agent.id, statebuffer_random)
    
    env.deal_cards()
    
    renderer = PyGameTrucoRenderer(statebuffer_human, human_agent.id, human_agent)
    
    event_agent_human = threading.Event()
    event_renderer_human = threading.Event()
    event_agent_random = threading.Event()
    event_renderer_random = threading.Event()
    
    thread_agent_human = threading.Thread(
        target=agent_thread,
        args=(human_agent, event_agent_human, event_renderer_human, 0.1),
        daemon=True
    )
    
    thread_agent_random = threading.Thread(
        target=agent_thread,
        args=(random_agent, event_agent_random, event_renderer_random, 0.1),
        daemon=True
    )
    
    thread_renderer = threading.Thread(
        target=renderer_thread,
        args=(renderer, event_agent_human, event_renderer_human, 0.1),
        daemon=True
    )
    
    thread_agent_human.start()
    thread_agent_random.start()
    thread_renderer.start()
    
    event_agent_human.set()
    event_agent_random.set()
    event_renderer_human.set()
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nJuego terminado por el usuario")


if __name__ == "__main__":
    main()
