from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import TimeLimit, TimeLimitMilliseconds

class Wait_CfgState(SlaveState):
    
    _self = None
    
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def checkTelegram(self):
        #TO-DO
        """"""
    
    def setParameters(self, slave, wd_on, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        slave.wd_limit = watchdog_ms
        slave.watchdog = TimeLimitMilliseconds(watchdog_ms)
        slave.slave_reaction_time = slave_reaction_time
        slave.reaction_timer = TimeLimitMilliseconds(slave_reaction_time)
        slave.freeze_mode_enable = freeze_mode_enable
        slave.locked = locked
        slave.group = group
        slave.master_add = master_add
        slave.id = id
    
    def setAddress(self, slave, address):
        raise SlaveException("Slave " + str(slave.getId) + " is in Wait Configuration state, can't accept address setting telegram!")

    def checkTelegramToSend(self, slave, telegram):
        """"""    