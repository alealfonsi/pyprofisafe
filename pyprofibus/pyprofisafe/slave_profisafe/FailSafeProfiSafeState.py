from pyprofibus.slave.FailSafeProfibusState import FailSafeProfibusState


class FailSafeProfiSafeState(FailSafeProfibusState):
    
    def enterPassivation(self, slave):
        """TODO"""

    #override
    def checkTelegram(self, slave, telegram):
        """TODO"""
    
    #override
    def checkTelegramToSend(self, slave, telegram):
        """TODO"""