from pyprofibus.dp.dp import DpTelegram_DataExchange_Req, DpTelegram_GlobalControl
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
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
        """TODO"""
    
    def handleEvent(self, slave, telegram):
        """TODO"""