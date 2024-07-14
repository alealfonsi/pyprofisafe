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