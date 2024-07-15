from pyprofibus.dp.dp import DpTelegram_ChkCfg_Req, DpTelegram_DataExchange_Req, DpTelegram_GetCfg_Req, DpTelegram_SetPrm_Req, DpTelegram_SlaveDiag_Req
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteHost import ControlByteHost
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram import ProfiSafeTelegram
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError


class ProfiSafeTelegram_Req(ProfiSafeTelegram):
    
    def __init__(self, payload, control_byte, crc):
        super().__init__(crc)
        self.control_byte = control_byte
        if (
            DpTelegram_DataExchange_Req.checkType(payload)
            or DpTelegram_SlaveDiag_Req.checkType(payload)
            or DpTelegram_SetPrm_Req.checkType(payload)
            or DpTelegram_ChkCfg_Req.checkType(payload)
            or DpTelegram_GetCfg_Req.checkType(payload)
        ):
            self.payload = payload
        else:
            raise ProfiSafeError("Cannot instantiate %s with a %s !" % (self.__class__, payload.__class__))
        