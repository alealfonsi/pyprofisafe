from abc import ABC, abstractmethod
from collections import deque

class CpPhyInterface(ABC):
    @abstractmethod
    def sendData(self, telegramData, srd):
        pass

    @abstractmethod
    def pollData(self, timeout):
        pass

    @abstractmethod
    def poll(self, timeout=0.0):
        pass

    @abstractmethod
    def send(self, telegram, srd, maxReplyLen=-1):
        pass

    @abstractmethod
    def setConfig(self, baudrate=9600):
        pass

    @abstractmethod
    def releaseBus(self):
        pass

    @abstractmethod
    def clearTxQueueAddr(self, da):
        pass

    @abstractmethod
    def __monotonic_time(self):
        pass