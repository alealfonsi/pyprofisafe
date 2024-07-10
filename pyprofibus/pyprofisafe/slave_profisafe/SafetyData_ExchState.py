from pyprofibus.dp.dp import DpTelegram_DataExchange_Req, DpTelegram_GlobalControl
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteHost import ControlByteHost
from pyprofibus.pyprofisafe.slave_profisafe.FailSafeProfiSafeState import FailSafeProfiSafeState
from pyprofibus.slave.Data_ExchState import Data_ExchState


class SafetyData_ExchState(Data_ExchState):

    #override
    def checkTelegram(self, slave, telegram):
        if not telegram.payload.sa == slave.getMasterAddress():
            print("Not my master")
            return False
        if (
             DpTelegram_DataExchange_Req.checkType(telegram.payload) or
             DpTelegram_GlobalControl.checkType(telegram.payload)
            ):
            if telegram.control_byte.isClear():
                slave.setRxTelegram(telegram)
                return True
            else:
                self.handleEvent(slave, telegram)
        else:
             raise ProfiSafeError("Slave " + str(slave.getId()) + """ is in 
                                      Data Exchange (ProfiSafe) state and received a proper telegram at the fdl level 
                                    but not handled at the dp level (either wrong or not yet handled by the library)\n
                                      Telegram: %s""" % str(telegram))

    #override
    def checkTelegramToSend(self, slave, telegram):
        super().checkTelegramToSend(slave, telegram.payload)
    
    def handleOperatorAckRequested(self):
        """TODO"""
    
    def handleResetMNR(self):
        """TODO"""
    
    def handleActivateFailSafeValues(self, slave):
        slave.setState(FailSafeProfiSafeState(slave))        
    
    def handleEvent(self, slave, telegram):
        status = telegram.control_byte.data
        if ControlByteHost.OPERATOR_ACK_REQUESTED & status:
            self.handleOperatorAckRequested()
        if ControlByteHost.RESET_MNR & status:
            self.handleResetMNR()
        if ControlByteHost.ACTIVATE_FV & status:
            self.handleActivateFailSafeValues()