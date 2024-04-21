from abc import ABC, abstractmethod

class FdlTelegramInterface(ABC):
    """Interface for FdlTelegram."""

    @classmethod
    @abstractmethod
    def getSizeFromRaw(cls, data):
        """Get size from raw data."""
        pass

    @abstractmethod
    def getRealDuLen(self):
        """Get real length of DU field."""
        pass

    @staticmethod
    @abstractmethod
    def calcFCS(data):
        """Calculate Frame Check Sequence."""
        pass

    @abstractmethod
    def getRawData(self):
        """Get raw data."""
        pass

    @staticmethod
    @abstractmethod
    def __duExtractAe(du):
        """Extract address extension bytes from DU."""
        pass

    @staticmethod
    @abstractmethod
    def fromRawData(data):
        """Create FdlTelegram object from raw data."""
        pass

    @classmethod
    @abstractmethod
    def checkType(cls, telegram):
        """Check if the object is an instance of FdlTelegram."""
        pass
