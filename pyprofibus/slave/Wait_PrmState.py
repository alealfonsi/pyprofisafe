from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import TimeLimit, TimeLimitMilliseconds

class Wait_PrmState(SlaveState):

    def setParameters(self, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        slave = self.getSlave()
        slave.watchdog = TimeLimitMilliseconds(watchdog_ms)
        slave.slave_reaction_time = slave_reaction_time
        slave.freeze_mode_enable = freeze_mode_enable
        slave.locked = locked
        slave.group = group
        slave.master_add = master_add
        slave.id = id
    
    def setAddress(self, address):
        raise SlaveException("Slave " + str(self.getSlave().getId) + " is in Wait Parameterization state, can't accept address setting telegram!")