from pyprofibus.slave.SlaveState import SlaveState


class FailSafeProfibusState(SlaveState):

    need_reparameterization: bool
    
    def __init__(self, need_reparameterization):
        self.__clearOutputs()
        self.need_reparameterization = need_reparameterization
        
    
    def __clearOutputs():
        """"""