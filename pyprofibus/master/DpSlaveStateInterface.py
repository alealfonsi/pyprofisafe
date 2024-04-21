from abc import ABC, abstractmethod

class DpSlaveStateInterface(ABC):
    """Interface for managing the runtime state of a DP slave."""

    @abstractmethod
    def getRxQueue(self):
        """Get the received telegrams queue and clear it.

        Returns:
            list: List of received telegrams.
        """
        pass

    @abstractmethod
    def flushRxQueue(self):
        """Clear the received telegrams queue."""
        pass

    @abstractmethod
    def getState(self):
        """Get the current state of the DP slave.

        Returns:
            int: Current state of the DP slave.
        """
        pass

    @abstractmethod
    def getNextState(self):
        """Get the next state of the DP slave.

        Returns:
            int: Next state of the DP slave.
        """
        pass

    @abstractmethod
    def setState(self, state, stateTimeLimit=None):
        """Set the state of the DP slave.

        Args:
            state (int): The state to set for the DP slave.
            stateTimeLimit (float, optional): Time limit for the state (in seconds).
                                              Defaults to None.
        """
        pass

    @abstractmethod
    def applyState(self):
        """Apply the new state to the DP slave."""
        pass

    @abstractmethod
    def stateJustEntered(self):
        """Check if the state was just entered.

        Returns:
            bool: True if the state was just entered, False otherwise.
        """
        pass

    @abstractmethod
    def stateIsChanging(self):
        """Check if the state is changing.

        Returns:
            bool: True if the state is changing, False otherwise.
        """
        pass

    @abstractmethod
    def restartStateTimeout(self, timeout=None):
        """Restart the timeout for the current state.

        Args:
            timeout (float, optional): Timeout duration (in seconds). 
                                       Defaults to None.
        """
        pass

    @abstractmethod
    def stateHasTimeout(self):
        """Check if the current state has timed out.

        Returns:
            bool: True if the current state has timed out, False otherwise.
        """
        pass
