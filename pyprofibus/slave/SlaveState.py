from abc import ABC, abstractmethod

from pyprofibus.slave.Slave import Slave
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

    __slave: Slave = None

    def getSlave(self):
        return self.__slave
    
    def setSlave(self, slave):
        self.__slave = Slave

    @abstractmethod
    def setParameters(self,
                watchdog_ms: int,
                slave_reaction_time, 
                freeze_mode_enable,
                locked, 
                group, 
                master_add,
                id): 
        """
        Sets the 7 mandatory parameter for a slave
        """
    
    @abstractmethod
    def setAddress(self, address):
        """
        Sets the address of the slave at start up
        """