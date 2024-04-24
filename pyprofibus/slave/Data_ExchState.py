from pyprofibus.dp.dp import DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram, FdlTelegram_var
from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState

class Data_ExchState(SlaveState):

    def checkTelegram(self, telegram):
            if FdlTelegram_var.checkType(telegram):
                return self.__checkDpTelegram(telegram)
            elif telegram.da == FdlTelegram.ADDRESS_MCAST:
                #TO-DO
                #self.__handleMcastTelegram(telegram)
                """"""
            elif False:
                #TO-DO
                 """Whatever other kind of fdl frame type accepted in this state...TO-DO later"""
            else:
                raise SlaveException("Slave " + str(self.getSlave().getId()) + """ is in 
                                      Data Exchange state and can't accept this type of telegram.\n
                                      Telegram: %s""" % str(telegram))

    
    def __checkDpTelegram(self, telegram):
        #check if something with field check bit is important before this step
        if DpTelegram_DataExchange_Req.checkType(telegram):
            self.getSlave().setRxTelegram(telegram)
            return True
            #self.__handleDataExchangeRequest(telegram)
        elif False:
             #TO-DO
             """Whatever other kind of dp frame accepted in this state...TO-DO later"""
        else:
             raise SlaveException("Slave " + str(self.getSlave().getId()) + """ is in 
                                      Data Exchange state and received a proper telegram at the fdl level 
                                    but not handled at the dp level (either wrong or not yet handled by the library)\n
                                      Telegram: %s""" % str(telegram))
    
    def checkTelegramToSend(self, telegram):
        if (DpTelegram_DataExchange_Con.checkType(telegram)
            and DpTelegram_DataExchange_Req.checkType(self.getSlave().getRxTelegram())):
             #some other check?
             return
        elif False:
             #TO-DO
             """Whatever other type of frame accepted in this state"""
        else:
             raise SlaveException("Slave " + str(self.getSlave().getId()) + """ is in 
                                      Data Exchange state. Cannot send this kind of telegram\n
                                      Telegram: %s""" % str(telegram))
        
    #def __handleDataExchangeRequest(self, telegram):
    #    # Here the handling of the meaning of the telegram has to be done
    #    # At the moment, this method is implemented just answering to the master with a standard frame
    #    # of the proper type
    #    response_telegram = DpTelegram_DataExchange_Con(da = self.getSlave().getMasterAddress(),
    #                                                    sa = self.getAddress(),
    #                                                    fc = FdlTelegram.FC_DL,
    #                                                    du = b"\x00\x00\x00\x00")
    #    #TO-DO send the telegram
        
        
    def setParameters(self, watchdog, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept parameterization!")

    def setAddress(self, address):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept address setting telegram!")