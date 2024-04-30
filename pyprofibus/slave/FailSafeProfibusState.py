from pyprofibus.dp.dp import DpTelegram_DataExchange_Req, DpTelegram_GlobalControl, DpTelegram_SetPrm_Req
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.slave.Wait_PrmState import Wait_PrmState


class FailSafeProfibusState(SlaveState):

    need_reparameterization: bool
    _self = None
    
    def __new__(cls, slave):
        if cls._self is None:
            cls._self = super().__new__(cls)
        cls._self.setSlave(slave)
        return cls._self
    
    def __init__(self):
        self.__setFailSafeProcessVariables()
        self.__clearOutputs()
        self.need_reparameterization = self.getSlave().wd_expired
        print("Slave " + self.getSlave().getId() + " is entering fail safe state (Profibus)")
    
    def checkTelegram(self, telegram):
        if self.need_reparameterization == True:
            if DpTelegram_SetPrm_Req.checkType(telegram):
                self.getSlave().setState(Wait_PrmState())
                return self.getSlave().checkTelegram(telegram)
            else:
                raise SlaveException("Slave " + str(self.getSlave().getId()) + """
                                     is in Fail safe mode and needs reparameterization but
                                     didn't receive the proper tg.\n Telegram: %s""" % str(telegram))
        else:
            return self.__check(telegram)
    
    def __check(self, telegram):
        if DpTelegram_DataExchange_Req.checkType(telegram):
            if telegram.getDU() is not None:
                raise SlaveException("Slave " + str(self.getSlave().getId()) + """
                                     is in Fail safe mode but received a data exchange request
                                     with payload.\n Telegram: %s""" % str(telegram))
            self.getSlave().setRxTelegram(telegram)
            return True
        elif DpTelegram_GlobalControl.checkType(telegram):
            if telegram.controlCommand != DpTelegram_GlobalControl.CCMD_OPERATE:
                raise SlaveException("Slave " + str(self.getSlave().getId()) + """
                                     is in Fail safe mode but received a global control telegram
                                     whose command is not CCMD_OPERATE.\n Telegram: %s""" % str(telegram))
            self.getSlave().setState(Data_ExchState())
            self.getSlave().setRxTelegram(telegram)
            return True
        else:
             raise SlaveException("Slave " + str(self.getSlave().getId()) + """ is in 
                                      Fail safe mode and received a proper telegram at the fdl level 
                                    but not handled at the dp level (either wrong or not yet handled by the library)\n
                                      Telegram: %s""" % str(telegram))
            
    def __clearOutputs():
        """TO-DO"""

    def __setFailSafeProcessVariables():
        """TO-DO"""