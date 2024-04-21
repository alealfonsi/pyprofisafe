from abc import ABC, abstractmethod

class DpSlaveDescInterface(ABC):
    """Interface for managing the static descriptor data of a DP slave."""

    @abstractmethod
    def setCfgDataElements(self, cfgDataElements):
        """Set DpCfgDataElement()s from the specified list in the Chk_Cfg telegram.

        Args:
            cfgDataElements (list): List of DpCfgDataElement()s.
        """
        pass

    @abstractmethod
    def setUserPrmData(self, userPrmData):
        """Set the User_Prm_Data of the Set_Prm telegram.

        Args:
            userPrmData: User parameter data.
        """
        pass

    @abstractmethod
    def setSyncMode(self, enabled):
        """Enable/disable sync-mode. Must be called before parameterisation.

        Args:
            enabled (bool): Whether to enable sync-mode or not.
        """
        pass

    @abstractmethod
    def setFreezeMode(self, enabled):
        """Enable/disable freeze-mode. Must be called before parameterisation.

        Args:
            enabled (bool): Whether to enable freeze-mode or not.
        """
        pass

    @abstractmethod
    def setGroupMask(self, groupMask):
        """Assign the slave to one or more groups. Must be called before parameterisation.

        Args:
            groupMask: Group mask.
        """
        pass

    @abstractmethod
    def setWatchdog(self, timeoutMS):
        """Set the watchdog timeout (in milliseconds). If timeoutMS is 0, the watchdog is disabled.

        Args:
            timeoutMS (int): Watchdog timeout in milliseconds.
        """
        pass

    @abstractmethod
    def setMasterOutData(self, data):
        """Set the master-out-data that will be sent the next time we are able to send something to that slave.

        Args:
            data: Data to be sent.
        """
        pass

    @abstractmethod
    def getMasterInData(self):
        """Get the latest received master-in-data.

        Returns:
            object: Latest received master-in-data.
        """
        pass

    @abstractmethod
    def isConnecting(self):
        """Check if the slave is in the process of getting connected/configured.

        Returns:
            bool: True if the slave is connecting, False otherwise.
        """
        pass

    @abstractmethod
    def isConnected(self):
        """Check if the slave is fully connected and Data_Exchange or periodic slave diagnosis is currently running.

        Returns:
            bool: True if the slave is connected, False otherwise.
        """
        pass
