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
    
    @classmethod
    def checkType(cls, telegram):
        return isinstance(telegram, cls)
    

