from pyprofibus.slave.SlaveInterface import SlaveInterface
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import ProfibusError, TimeLimit, TimeLimitMilliseconds

class Slave(SlaveInterface):
    
    __state: SlaveState = None
    
    address: int = 126
    watchdog: TimeLimitMilliseconds = None
    slave_reaction_time: int = None
    freeze_mode_enable: bool = None
    locked: bool = None
    group: int = None
    master_add: int = None
    id: str = None

    def getState(self):
        return self.__state
    
    def setState(self, state: SlaveState):
        self.__state = state
    
    def getId(self):
        return self.id

    def setAddress(self, address):
        self.address = address

    def setParameters(self, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        self.__state.setParameters(self, watchdog_ms, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id)

class SlaveException(ProfibusError):
    def __init__(self, message):
        super().__init__(message)








