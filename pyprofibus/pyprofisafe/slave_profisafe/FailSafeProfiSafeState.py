from pyprofibus.dp.dp import DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req, DpTelegram_GlobalControl
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteDevice import ControlByteDevice
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Con import ProfiSafeTelegram_Con
from pyprofibus.slave.FailSafeProfibusState import FailSafeProfibusState


class FailSafeProfiSafeState(FailSafeProfibusState):

    _self = None
    
    def __new__(cls, slave=None):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self
    
    def __init__(self, slave):
        self.need_reparameterization = False
        super().enterFailSafeState(slave)
        print("Slave " + slave.getId() + " is entering fail safe state (ProfiSafe)")
    
    #override
    def checkTelegram(self, slave, telegram):
        from pyprofibus.pyprofisafe.slave_profisafe.SafetyData_ExchState import SafetyData_ExchState

        if DpTelegram_DataExchange_Req.checkType(telegram.payload):
            for b in telegram.payload.getDU():
                if b != '\x00':
                    raise ProfiSafeError("Slave " + str(slave.getId()) + """
                                     is in Fail Safe mode but received a data exchange request
                                     with payload different from 0s.\n Telegram: %s""" % str(telegram))    
            slave.setRxTelegram(telegram)
            self.sendResponse(slave)
            return True
        elif DpTelegram_GlobalControl.checkType(telegram.payload):
            if telegram.payload.controlCommand != DpTelegram_GlobalControl.CCMD_OPERATE:
                raise ProfiSafeError("Slave " + str(slave.getId()) + """
                                     is in Fail safe mode but received a global control telegram
                                     whose command is not CCMD_OPERATE.\n Telegram: %s""" % str(telegram))
            slave.setState(SafetyData_ExchState())
            slave.setRxTelegram(telegram)
            return True
        else:
             raise ProfiSafeError("Slave " + str(slave.getId()) + """ is in 
                                      Fail safe mode and received a proper telegram at the fdl level 
                                    but not handled at the dp level (either wrong or not yet handled by the library)\n
                                      Telegram: %s""" % str(telegram))
    
    #override
    def checkTelegramToSend(self, slave, telegram):
        if not ProfiSafeTelegram_Con.checkType(telegram):
            raise ProfiSafeError("Trying to send a tg that is not profisafe")
        super().checkTelegramToSend(slave, telegram.payload)

    #override
    def sendResponse(self, slave):
        payload = DpTelegram_DataExchange_Con(da=slave.getMasterAddress(),
                                                    sa=slave.address,
                                                    fc=FdlTelegram.FC_OK,
                                                    du=bytearray((0x00, 0x00)))
        control_byte = ControlByteDevice(0x00)
        #create a proper crc here
        crc = b'\xab' * 24
        telegram = ProfiSafeTelegram_Con(payload, control_byte, crc)
        slave.ps_trans.send(telegram)