from pyprofibus.fieldbus_data_link.fdl import FdlTelegram, FdlTelegram_var
from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState

class Data_ExchState(SlaveState):

    def __checkTelegram(self, telegram):
            if FdlTelegram_var.checkType(telegram):
                """slave.fcb.handleReply()"""
            elif telegram.da == FdlTelegram.ADDRESS_MCAST:
                #TO-DO
                #self.__handleMcastTelegram(telegram)
                """"""
            elif 0:
                #TO-DO
                 """Whatever other kind of frame type accepted in this state...TO-DO later"""
            else:
                 raise SlaveException("Slave " + str(self.getSlave().getId()) + """ is in 
                                      Data Exchange state and can't accept this type of telegram.
                                      Telegram: %s""" % str(telegram))
        
    def setParameters(self, watchdog, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept parameterization!")

    def setAddress(self, address):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept address setting telegram!")