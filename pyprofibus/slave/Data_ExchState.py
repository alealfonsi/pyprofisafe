from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState

class Data_ExchState(SlaveState):

    def setParameters(self, watchdog, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept parameterization!")

    def setAddress(self, address):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept address setting telegram!")