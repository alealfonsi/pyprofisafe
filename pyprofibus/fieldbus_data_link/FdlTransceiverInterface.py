from abc import ABC, abstractmethod

class FdlTransceiverInterface(ABC):
    """Interface for FdlTransceiver."""

    @abstractmethod
    def setRXFilter(self, newFilter):
        """Set the RX filter."""
        pass

    @abstractmethod
    def poll(self, timeout=0.0):
        """Poll for incoming telegrams."""
        pass

    @abstractmethod
    def send(self, fcb, telegram):
        """Send an FdlTelegram."""
        pass
