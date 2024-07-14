from pyprofibus.dp.dp import DpTelegram_GlobalControl, DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlFCB
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram import ProfiSafeTelegram
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Con import ProfiSafeTelegram_Con
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_GlobalControl import ProfiSafeTelegram_GlobalControl
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Req import ProfiSafeTelegram_Req


class ProfiSafeTransceiver():

    dp_trans: DpTransceiver

    def __init__(self, dp_trans):
        self.dp_trans = dp_trans

    def poll(self, timeout = 0.0):
        telegram = None
        #safety_wrapper = self.dp_trans.fdlTrans.phy.getSerial().read(40)
        ok, payload = self.dp_trans.poll(timeout)
        if ok and payload:
            safety_wrapper = self.dp_trans.fdlTrans.phy.getSerial().read(4)
            if len(safety_wrapper) == 4:
                control_byte = safety_wrapper[0]
                crc = safety_wrapper[1:4]
                self.checkCRC(crc)
                if DpTelegram_GlobalControl.checkType(payload):
                    telegram = ProfiSafeTelegram_GlobalControl(payload, control_byte, crc)
                else:
                    #fai un factory
                    try:
                        telegram = ProfiSafeTelegram_Req(payload, control_byte, crc)
                    except ProfiSafeError:
                        telegram = ProfiSafeTelegram_Con(payload, control_byte, crc)
            else:
                ok = False
        return (ok, telegram)


    def send(self, telegram):
        if (ProfiSafeTelegram_Req.checkType(telegram)
            or ProfiSafeTelegram_Con.checkType(telegram)
            or ProfiSafeTelegram_GlobalControl.checkType(telegram)):
            self.dp_trans.send(FdlFCB(False), telegram.payload)
            self.dp_trans.fdlTrans.phy.sendData(telegram.control_byte.data, None)
            self.dp_trans.fdlTrans.phy.sendData(telegram.crc, None)
        else:        
            self.dp_trans.send(False, telegram)
    
    def checkCRC(self, crc):
        for b in crc:
            if b != 0xab:
                raise ProfiSafeError("CRC Error!")
