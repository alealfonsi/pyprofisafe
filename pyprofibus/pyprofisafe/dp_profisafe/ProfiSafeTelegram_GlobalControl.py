from pyprofibus.dp.dp import DpTelegram_GlobalControl
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteHost import ControlByteHost
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram import ProfiSafeTelegram


class ProfiSafeTelegram_GlobalControl(ProfiSafeTelegram):

    def __init__(self, payload, control_byte, crc):
        super().__init__(crc)
        self.control_byte = ControlByteHost(control_byte)
        if DpTelegram_GlobalControl.checkType(payload):
            self.payload = payload
        else:
            raise ProfiSafeError("Cannot instantiate %s with a %s !" % (self.__class__, payload.__class__))
    
