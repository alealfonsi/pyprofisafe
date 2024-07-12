import time
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteDevice import ControlByteDevice
from pyprofibus.pyprofisafe.slave_profisafe.SafetyData_ExchState import SafetyData_ExchState
from pyprofibus.slave.SlaveState import SlaveState


class PassivationState(SlaveState):

    _self = None
    
    def __new__(cls, slave=None):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self
    
    def __init__(self, slave):
        print("Slave " + slave.getId() + " is entering Passivation!")
        time.sleep(1)
        print("Fault is cleared...")
        print("Press ENTER to reintegrate the device.")
        input()
        slave.setState(SafetyData_ExchState())
    
    #override
    def receive(self, slave, timeout):
        print("Slave " + slave.getId() + """is in Passivation state and
              cannot receive any telegram!""")
    
    #override
    def send(self, slave, telegram, dpTrans):
        print("Slave " + slave.getId() + """is in Passivation state and
              cannot send any telegram!""")