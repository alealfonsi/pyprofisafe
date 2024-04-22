from pyprofibus.slave.SlaveInterface import SlaveInterface
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import ProfibusError, TimeLimit

class Slave(SlaveInterface):
    
    __state = None

    watchdog = None
    slave_reaction_time = None
    freeze_mode_enable = None
    locked = None
    group = None
    master_add = None
    id = None

    def getState(self):
        return self.__state
    
    def setState(self, state: SlaveState):
        self.__state = state

    def setParameters(self, watchdog_ms: int, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        self.__state.setParameters(self, watchdog_ms, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id)

class SlaveException(ProfibusError):
    def __init__(self, message):
        super().__init__(message)








