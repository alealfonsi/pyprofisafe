from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveState import SlaveState

class Wait_PrmState(SlaveState):

    def setParameters(slave: Slave, watchdog, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        slave.watchdog = watchdog
        slave.slave_reaction_time = slave_reaction_time
        slave.freeze_mode_enable = freeze_mode_enable
        slave.locked = locked
        slave.group = group
        slave.master_add = master_add
        slave.id = id