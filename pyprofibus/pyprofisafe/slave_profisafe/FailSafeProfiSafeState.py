import time
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
        crc = b'\xab' * 3
        telegram = ProfiSafeTelegram_Con(payload, control_byte, crc)
        slave.ps_trans.send(telegram)
    
    #override
    def receive(self, slave, timeout):
        try:
            ok, telegram = slave.ps_trans.poll(timeout)
        except ProfiSafeError as e:
            print("RX error: %s" % str(e))
            return False
        if ok and telegram:
            if (telegram.payload.da == self.getAddress(slave)) or (telegram.payload.da == FdlTelegram.ADDRESS_MCAST):
                if self.checkTelegram(slave, telegram):
                    slave.resetWatchdog()
                    print("""XXX| Slave %s in state %s received frame of type %s at time: %d\n
                      XXX| %s""" % (slave.getId(), self.__class__, telegram.__class__, time.time(), telegram))
                    return True
        else:
            if telegram:
                print("XXX| Slave %s in state %s received corrupt telegram at time: %d\nXXX| %s" 
          			% (slave.getId(), self.__class__, time.time(), telegram))
            return False
    
    #override
    def send(self, slave, telegram):
        try:
            self.checkTelegramToSend(slave, telegram)
            slave.ps_trans.send(telegram) 
            #fcb is passed as disabled
            #this feature is not really part of Profibus DP, but of the 
            #standard Profibus. It will be useful with profisafe because
            #its functioning is very similar to the virtual monitoring number
        except ProfiSafeError as e:
        	print(str(e))