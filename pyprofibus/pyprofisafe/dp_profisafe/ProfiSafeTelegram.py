from abc import ABC

from pyprofibus.dp.dp import DpTelegram
from pyprofibus.pyprofisafe.dp_profisafe.CRC_Manager import CRC_Manager
from pyprofibus.pyprofisafe.dp_profisafe.ControlByte import ControlByte


class ProfiSafeTelegram(ABC):

    payload: DpTelegram
    control_byte: ControlByte
    crc: bytearray
    virtual_monitoring_number: int

    crc_manager: CRC_Manager

    def __init__(self, crc):
        self.crc = crc
    
    def checkType(self, telegram):
        if isinstance(telegram, self.__class__):
            return True
        return False
    

