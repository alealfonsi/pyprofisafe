#from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.slave.Wait_PrmState import Wait_PrmState

class ResetState(SlaveState):
    
    _self = None
    
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def checkTelegram(self):
        #TO-DO
        """"""

    def setParameters(self, slave, watchdog, slave_reaction_time: int, freeze_mode_enable: bool, locked: bool, group, master_add: int, id: int):
        raise SlaveException("Slave " + str(slave.getId()) + " is in Reset state, can't accept parameterization!")
        
    def setAddress(self, slave, address):
        if address < 0 or address > 125:
            raise SlaveException("Address not valid! (not in range 0 - 125)")
        else:
            slave.address = address
            slave.setState(Wait_PrmState())
        
    def checkTelegramToSend(self, slave, telegram):
        """"""