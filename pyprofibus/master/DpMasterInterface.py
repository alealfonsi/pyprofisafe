from abc import ABC, abstractmethod

class DpMasterInterface(ABC):
    @abstractmethod
    def destroy(self):
        """
        Close the physical layer connection.
        """

    @abstractmethod
    def addSlave(self, slaveDesc):
        """
        Register a slave.

        Args:
            slaveDesc (DpSlaveDesc): Description of the slave to be registered.

        Raises:
            DpError: If the slave is already registered or has an unsupported input size.
        """

    @abstractmethod
    def getSlaveList(self):
        """
        Get a list of registered DpSlaveDescs, sorted by address.

        Returns:
            list: List of registered DpSlaveDescs.
        """

    @abstractmethod
    def initialize(self):
        """
        Initialize the DP-Master.
        """

    @abstractmethod
    def syncMode(self, groupMask):
        """
        Set SYNC-mode on the specified groupMask.

        Args:
            groupMask (int): Group mask indicating which slaves to address. If 0, all slaves are addressed.
        """

    @abstractmethod
    def syncModeCancel(self, groupMask):
        """
        Cancel SYNC-mode on the specified groupMask.

        Args:
            groupMask (int): Group mask indicating which slaves to address. If 0, all slaves are addressed.
        """

    @abstractmethod
    def freezeMode(self, groupMask):
        """
        Set FREEZE-mode on the specified groupMask.

        Args:
            groupMask (int): Group mask indicating which slaves to address. If 0, all slaves are addressed.
        """

    @abstractmethod
    def freezeModeCancel(self, groupMask):
        """
        Cancel FREEZE-mode on the specified groupMask.

        Args:
            groupMask (int): Group mask indicating which slaves to address. If 0, all slaves are addressed.
        """

    @abstractmethod
    def _setToSlaveData(self, slaveDesc, data):
        """
        Set the master-out-data that will be sent the next time data exchange occurs with a specific slave.

        Args:
            slaveDesc (DpSlaveDesc): Description of the slave.
            data (bytes): Data to be sent to the slave.

        Raises:
            DpError: If the data size does not match the slave's configured input size.
        """

    @abstractmethod
    def _getFromSlaveData(self, slaveDesc):
        """
        Get the latest received master-in-data from a specific slave.

        Args:
            slaveDesc (DpSlaveDesc): Description of the slave.

        Returns:
            bytes or None: Received data from the slave, or None if no data has been received.
        """

    @abstractmethod
    def _slaveIsConnecting(self, slaveDesc):
        """
        Check if a specific slave is in the process of connecting.

        Args:
            slaveDesc (DpSlaveDesc): Description of the slave.

        Returns:
            bool: True if the slave is connecting, False otherwise.
        """

    @abstractmethod
    def _slaveIsConnected(self, slaveDesc):
        """
        Check if a specific slave is connected.

        Args:
            slaveDesc (DpSlaveDesc): Description of the slave.

        Returns:
            bool: True if the slave is connected, False otherwise.
        """
