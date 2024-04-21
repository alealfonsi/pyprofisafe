from abc import ABC, abstractmethod

class DpTelegramInterface(ABC):
    """Interface for DpTelegram."""

    @abstractmethod
    def toFdlTelegram(self):
        """Convert the DpTelegram to an FdlTelegram."""
        pass

    @classmethod
    @abstractmethod
    def extractSAP(cls, ae):
        """Extract the SSAP/DSAP from SAE/DAE."""
        pass

    @classmethod
    @abstractmethod
    def extractSegmentAddr(cls, ae):
        """Extract the segment address from SAE/DAE."""
        pass

    @classmethod
    @abstractmethod
    def fromFdlTelegram(cls, fdl, thisIsMaster):
        """Create a DP telegram from an FDL telegram."""
        pass

    @abstractmethod
    def getDU(self):
        """Get Data-Unit."""
        pass

    @classmethod
    @abstractmethod
    def checkType(cls, telegram):
        """Check if the object is an instance of DpTelegram."""
        pass
