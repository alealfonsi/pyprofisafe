from pyprofibus.pyprofisafe.slave_profisafe.FailSafeProfiSafeState import FailSafeProfiSafeState
from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveException import WatchdogExpiredException
from pyprofibus.util import TimeLimitMilliseconds


class F_Device(Slave):
    
    def __init__(self, phy) -> None:
        super().__init__(phy)
        self.f_monitor_expired = False
    
    #override
    def watchdogExpired(self):
        self.f_monitor_expired = True
        self.setState(FailSafeProfiSafeState(self))
        self.getState().enterPassivation(self)
        self.watchdog = None
        raise WatchdogExpiredException("Slave " + self.id + ": F-Monitoring time expired!")

    def setSafetyParameters():
        """TODO"""
    
