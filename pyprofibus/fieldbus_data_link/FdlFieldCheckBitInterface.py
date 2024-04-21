from abc import ABC, abstractmethod

class FdlFieldCheckBitInterface(ABC):
    """Interface for FCB context."""

    @abstractmethod
    def resetFCB(self):
        """Reset FCB and related flags."""
        pass

    @abstractmethod
    def enableFCB(self, enabled=True):
        """Enable or disable FCB handling."""
        pass

    @abstractmethod
    def FCBnext(self):
        """Toggle FCB bit, set FCV to 1, and reset waiting for reply flag."""
        pass

    @abstractmethod
    def enabled(self):
        """Check if FCB handling is enabled."""
        pass

    @abstractmethod
    def bitIsOn(self):
        """Check if the FCB bit is set."""
        pass

    @abstractmethod
    def bitIsValid(self):
        """Check if the FCB is valid."""
        pass

    @abstractmethod
    def setWaitingReply(self):
        """Set the waiting for reply flag."""
        pass

    @abstractmethod
    def handleReply(self):
        """Handle reply: toggle FCB if waiting for a reply."""
        pass
