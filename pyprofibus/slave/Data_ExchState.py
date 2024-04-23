from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.slave.SlaveState import SlaveState

class Data_ExchState(SlaveState):

    def __checkTelegram(self):
        """
        dpTrans = self.getSlave().getDpTrans()

        try:
            ok, telegram = dpTrans.poll()
        except SlaveException as e:
            print("RX error: %s" % str(e))
            return
        if ok and telegram:
            if telegram.da == self.getAddress():


            if telegram.da == FdlTelegram.ADDRESS_MCAST:
                self.__handleMcastTelegram(telegram)
            elif telegram.da == self.masterAddr:
                if telegram.sa in self.__slaveStates:
                    slave = self.__slaveStates[telegram.sa]
                    slave.rxQueue.append(telegram)
                    slave.fcb.handleReply()
                else:
                    self.__debugMsg("Received telegram from "
                        "unknown station %d:\n%s" %(
                        telegram.sa, str(telegram)))
            else:
                self.__debugMsg("Received telegram for "
                    "foreign station:\n%s" % str(telegram))
        else:
            if telegram:
                self.__debugMsg("Received corrupt "
					"telegram:\n%s" % str(telegram))"""

    def setParameters(self, watchdog, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept parameterization!")

    def setAddress(self, address):
        raise SlaveException("Slave " + str(self.getSlave().getId()) + " is in Data Exchange state, can't accept address setting telegram!")