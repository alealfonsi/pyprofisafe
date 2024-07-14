import time
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.slave.SlaveState import SlaveState


class SafetyDeviceState(SlaveState):

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
