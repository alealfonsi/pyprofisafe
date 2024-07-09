from abc import ABC, abstractmethod


class ControlByte(ABC):

    def __init__(self, data):
        self.data = data
    
    @abstractmethod
    def isClear(self) -> bool:
        pass