from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState

class ResetState(SlaveState):

    def setParameters(slave: Slave, watchdog, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        raise SlaveException("Slave " + str(slave.getId()) + " is in Reset state, can't accept parameterization!")
        