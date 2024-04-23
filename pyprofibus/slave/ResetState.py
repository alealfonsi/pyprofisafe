from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.slave.Wait_PrmState import Wait_PrmState

class ResetState(SlaveState):

    def __checkTelegram(self):
        #TO-DO
        """"""

    def setParameters(self, watchdog, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Reset state, can't accept parameterization!")
        
    def setAddress(self, address):
        if address < 0 or address > 125:
            raise SlaveException("Address not valid! (not in range 0 - 125)")
        else:
            self.getSlave().setAddress(address)
            self.setState(Wait_PrmState())