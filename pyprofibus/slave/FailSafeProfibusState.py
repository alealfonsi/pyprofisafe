from pyprofibus.dp.dp import DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req, DpTelegram_GlobalControl, DpTelegram_SetPrm_Req
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.slave.Wait_PrmState import Wait_PrmState
import pyprofibus.slave


class FailSafeProfibusState(SlaveState):

    need_reparameterization: bool
    _self = None
    
    def __new__(cls, slave=None):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self
    
    def __init__(self, slave):
        self.need_reparameterization = slave.wd_expired
        print("Slave " + slave.getId() + " is entering fail safe state (Profibus)")
    
    def enterFailSafeState(self, slave):
        self.__setFailSafeProcessVariables()
        self.__clearOutputs()
        if self.need_reparameterization:
            self.__sendRequestDiagnosticTelegram(slave)

    
    def checkTelegram(self, slave, telegram):
        if self.need_reparameterization == True:
            if DpTelegram_SetPrm_Req.checkType(telegram):
                self.need_reparameterization = False
                slave.setState(Wait_PrmState())
                return slave.checkTelegram(telegram)
            else:
                raise SlaveException("Slave " + str(slave.getId()) + """
                                     is in Fail safe mode and needs reparameterization but
                                     didn't receive the proper tg.\n Telegram: %s""" % str(telegram))
        else:
            return self.__check(telegram)
    
    def __check(self, slave, telegram):
        #from pyprofibus.slave.Data_ExchState import Data_ExchState

        if DpTelegram_DataExchange_Req.checkType(telegram):
            for b in telegram.getDU():
                if b != '\x00':
                    raise SlaveException("Slave " + str(slave.getId()) + """
                                     is in Fail Safe mode but received a data exchange request
                                     with payload different from 0s.\n Telegram: %s""" % str(telegram))    
            slave.setRxTelegram(telegram)
            self.sendResponse(slave)
            return True
        elif DpTelegram_GlobalControl.checkType(telegram):
            if telegram.controlCommand != DpTelegram_GlobalControl.CCMD_OPERATE:
                raise SlaveException("Slave " + str(slave.getId()) + """
                                     is in Fail safe mode but received a global control telegram
                                     whose command is not CCMD_OPERATE.\n Telegram: %s""" % str(telegram))
            slave.setState(pyprofibus.slave.Data_ExchState())
            slave.setRxTelegram(telegram)
            return True
        else:
             raise SlaveException("Slave " + str(slave.getId()) + """ is in 
                                      Fail safe mode and received a proper telegram at the fdl level 
                                    but not handled at the dp level (either wrong or not yet handled by the library)\n
                                      Telegram: %s""" % str(telegram))
        
    def sendResponse(self, slave):
        send_telegram = DpTelegram_DataExchange_Con(da=slave.getMasterAddress(),
                                                    sa=slave.address,
                                                    fc=FdlTelegram.FC_OK,
                                                    du=bytearray((0x00, 0x00)))
        slave.send(send_telegram)
    
    def checkTelegramToSend(self, slave, telegram):
        if not DpTelegram_DataExchange_Con.checkType(telegram):
            raise SlaveException()
        return True

    def __sendRequestDiagnosticTelegram(self, slave):
        send_telegram = DpTelegram_DataExchange_Con(da=slave.getMasterAddress(),
                                                    sa=slave.address,
                                                    fc=FdlTelegram.FC_RDH,
                                                    du=bytearray((0x00, 0x00)))
        slave.send(send_telegram)


    def setAddress(self, slave, address):
        raise SlaveException("Slave " + str(slave.getId()) + " is in Wait Parameterization state, can't accept address setting telegram!")
    
    def setParameters(self, slave, wd_on, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        raise SlaveException("""ERROR: method setParameters called on slave %d 
                             that is in Fail Safe state!""" % slave.getId())
            
    def __clearOutputs(self):
        """TO-DO"""

    def __setFailSafeProcessVariables(self):
        """TO-DO"""