from pyprofibus.slave.Data_ExchState import Data_ExchState


class SafetyData_ExchState(Data_ExchState):

    #override
    def checkTelegram(self, slave, telegram):
        """TODO"""
    
    #override
    def checkTelegramToSend(self, slave, telegram):
        """TODO"""