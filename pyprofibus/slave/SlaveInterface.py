from abc import ABC, abstractmethod

class SlaveInterface(ABC):

    @abstractmethod
    def setParameters(self,
                watchdog,
                slave_reaction_time: int, 
                freeze_mode_enable: bool,
                locked: bool, 
                group, 
                master_add: int,
                id: int): 
        """
        Sets the 7 mandatory parameter for a slave
        """