from pyprofibus.dp.dp import DpTelegram_DataExchange_Con, DpTelegram_GetCfg_Con, DpTelegram_SlaveDiag_Con
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteDevice import ControlByteDevice
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram import ProfiSafeTelegram
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError


class ProfiSafeTelegram_Con(ProfiSafeTelegram):

    def __init__(self, payload, control_byte, crc):
        super(crc)
        if isinstance(control_byte, ControlByteDevice):
            self.control_byte = control_byte
            if (
                DpTelegram_DataExchange_Con.checkType(payload)
                or DpTelegram_SlaveDiag_Con.checkType(payload)
                or DpTelegram_GetCfg_Con.checkType(payload)
            ):
                self.payload = payload
            else:
                raise ProfiSafeError("Cannot instantiate %s with a %s !" % (self.__class__, payload.__class__))
        else:
            raise ProfiSafeError("Cannot instantiate %s with a %s !" % (self.__class__, control_byte.__class__))
        