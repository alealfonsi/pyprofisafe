from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import TimeLimit, TimeLimitMilliseconds

class Wait_CfgState(SlaveState):
    
    def setParameters(slave: Slave, watchdog_ms: int, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        slave.watchdog = TimeLimitMilliseconds(watchdog_ms)
        slave.slave_reaction_time = slave_reaction_time
        slave.freeze_mode_enable = freeze_mode_enable
        slave.locked = locked
        slave.group = group
        slave.master_add = master_add
        slave.id = id