import time
from pyprofibus.dp.dp import DpTelegram, DpTelegram_GlobalControl, DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlTransceiver
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.FailSafeProfibusState import FailSafeProfibusState
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.SlaveException import WatchdogExpiredException
from pyprofibus.slave.SlaveInterface import SlaveInterface
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import TimeLimitMilliseconds

class Slave(SlaveInterface):
    
    #state
    __state: SlaveState
    
    #parameters
    address: int = 126
    wd_limit: int
    reaction_timer: TimeLimitMilliseconds

    watchdog: TimeLimitMilliseconds
    slave_reaction_time: int
    freeze_mode_enable: bool
    locked: bool
    group: int
    master_add: int
    id: str

    #transceivers
    phy: CpPhySerial
    fdlTrans: FdlTransceiver
    dpTrans: DpTransceiver

    #telegrams
    rx_telegram: DpTelegram = None

    #diagnostics
    wd_expired: bool = False

    def __init__(self, phy) -> None:
        super().__init__()
        self.phy = phy
        self.fdlTrans = FdlTransceiver(phy)
        self.dpTrans = DpTransceiver(self.fdlTrans, thisIsMaster=False)

    
    def receive(self, timeout):
        received = False
        #timeout = time(seconds) waiting in receiving state, polling countinously
        while timeout > 0:
            time.sleep(0.4)
            if self.__state.receive(self, 0.01): #check the watchdog every 10ms
                received = True
                self.reaction_timer.start()           
                break
            if self.watchdog is not None and self.watchdog.exceed():
                self.watchdogExpired()
            timeout -= 0.01
        return received

            
    def send(self, telegram):
        while not self.reaction_timer.exceed():
            time.sleep(0.01)
        print("XXX| Slave %s in state %s sends frame of type [%s] at time: %d\nXXX| %s"
              % (self.id, self.__state.__class__, telegram.__class__, time.time(), telegram))
        return self.__state.send(self, telegram)
    
    def watchdogExpired(self):
        self.wd_expired = True
        self.__state = FailSafeProfibusState(self)
        self.__state.enterFailSafeState(self)
        self.watchdog = None
        raise WatchdogExpiredException("Slave " + self.id + ": watchdog expired!")

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
        self.__state.setAddress(self, address)
    
    def getAddress(self):
        return self.address
    
    def getDpTrans(self):
        return self.dpTrans
    
    def getMasterAddress(self):
        return self.master_add

    def setParameters(self, wd_on: bool, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        self.__state.setParameters(self, wd_on, watchdog_ms, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id)
   








