from abc import ABC, abstractmethod

from pyprofibus.slave.Slave import Slave
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

    __slave = None

    def getId(self):
        return self.__slave
    
    def setId(self, slave: Slave):
        self.__slave = Slave

    @abstractmethod
    def setParameters(slave: Slave,
                watchdog_ms: int,
                slave_reaction_time: int, 
                freeze_mode_enable: bool,
                locked: bool, 
                group, 
                master_add: int,
                id: int): 
        """
        Sets the 7 mandatory parameter for a slave
        """
    