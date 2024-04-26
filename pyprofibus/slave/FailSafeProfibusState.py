from pyprofibus.slave.SlaveState import SlaveState


class FailSafeProfibusState(SlaveState):

    need_reparameterization: bool
    
    def __init__(self, need_reparameterization):
        self.__setFailSafeProcessVariables()
        self.__clearOutputs()
        self.need_reparameterization = self.getSlave().wd_expired
            
    def __clearOutputs():
        """TO-DO"""

    def __setFailSafeProcessVariables():
        """TO-DO"""