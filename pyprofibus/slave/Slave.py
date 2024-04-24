from pyprofibus.dp.dp import DpTelegram, DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlTransceiver
from pyprofibus.physical.phy_interface import CpPhyInterface
from pyprofibus.slave.FailSafeHandler import FailSafeHandler
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.SlaveInterface import SlaveInterface
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import ProfibusError, TimeLimitMilliseconds

class Slave(SlaveInterface):
    
    #state
    __state: SlaveState
    
    #parameters
    master_address: int
    address: int = 126
    wd_limit: int

    watchdog: TimeLimitMilliseconds
    slave_reaction_time: int
    freeze_mode_enable: bool
    locked: bool
    group: int
    master_add: int
    id: str

    #transceivers
    phy: CpPhyInterface
    fdlTrans: FdlTransceiver
    dpTrans: DpTransceiver

    #telegrams
    rx_telegram: DpTelegram = None

    #diagnostics
    wd_expired: bool = False

    #fail-safe handler (application specific)
    fail_safe_handler: FailSafeHandler

    def __init__(self, phy, fail_safe_handler) -> None:
        super().__init__()
        self.fdlTrans = FdlTransceiver(self.phy)
        self.dpTrans = DpTransceiver(self.fdlTrans, thisIsMaster=True)
        self.fail_safe_handler = fail_safe_handler
    
    def receive(self, timeout):
        #timeout = time(seconds) waiting in receiving state, polling countinously
        while timeout >= 0:
            if self.__state.receive(self.dpTrans, 0.01): #check the watchdog every 10ms
                break
            if self.watchdog.exceed():
                self.watchdogExpired()
            timeout -= 0.01
            
    def send(self, telegram):
        return self.__state.send(telegram, self.dpTrans)
    
    def watchdogExpired(self):
        self.fail_safe_handler.setFailSafeProcessVariables()
        self.wd_expired = True
        self.__state = ResetState
        raise WatchdogExpiredException("Slave " + id + ": watchdog expired!")

    def resetWatchdog(self):
        self.watchdog.start(self.wd_limit)
    
    def getRxTelegram(self):
        return self.rx_telegram
    
    def setRxTelegram(self, telegram):
        self.rx_telegram = telegram

    def getState(self):
        return self.__state
    
    def setState(self, state: SlaveState):
        self.__state = state
    
    def getId(self):
        return self.id

    def setAddress(self, address):
        self.address = address
    
    def getDpTrans(self):
        return self.dpTrans
    
    def getMasterAddress(self):
        return self.master_address

    def setParameters(self, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        self.__state.setParameters(self, watchdog_ms, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id)

class SlaveException(ProfibusError):
    def __init__(self, message):
        super().__init__(message)

class WatchdogExpiredException(SlaveException):
    def __init__(self, message):
        super().__init__(message)   








