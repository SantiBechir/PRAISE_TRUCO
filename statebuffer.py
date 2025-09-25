import uuid
from abc import ABC, abstractmethod
from environments import SimulatedEnvironment


class IStateBuffer(ABC):
    def __init__(self):
        self._uuid = uuid.uuid1()
        self._state = None
        self.changed = False


    @property
    def id(self):
        return self._uuid.int

    @abstractmethod
    def update(self, state):
        pass

    @abstractmethod
    def get_state(self):
        pass

class StateBuffer(IStateBuffer):
    def __init__(self, agent_id: int, env: SimulatedEnvironment):
        super(StateBuffer, self).__init__()
        env.add_statebuffer(agent_id, self)

    def update(self, state):
        self.state = state
        self.changed = True

    def get_state(self):
        if self.changed:
            self.changed = False
            return self.state
        else:
            return None