from abc import ABC, abstractmethod

class DpTransceiverInterface(ABC):
    """Interface for DpTransceiver."""

    @abstractmethod
    def poll(self, timeout=0.0):
        """Poll for incoming telegrams."""
        pass

    @abstractmethod
    def send(self, fcb, telegram):
        """Send a DpTelegram."""
        pass
