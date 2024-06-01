from pyprofibus.dp.dp import DpTelegram_SetPrm_Req
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.slave.Wait_CfgState import Wait_CfgState
from pyprofibus.util import TimeLimit, TimeLimitMilliseconds

class Wait_PrmState(SlaveState):
    
    _self = None
    
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def checkTelegram(self, slave, telegram):
        if not DpTelegram_SetPrm_Req.checkType(telegram):
            raise SlaveException("""Slave %d is waiting for parameterization but received 
                                 telegram: %s""" % (slave.getId()), telegram)

        parameters: bytearray = telegram.getDU()
        station_status = parameters[0]
        self.setParameters(
            slave,
            station_status & telegram.STA_WD,
            10 * parameters[1] * parameters[2],
            parameters[3],
            False,
            station_status & telegram.STA_LOCK, #this one is more complex but good enough for now
            parameters[6],
            telegram.sa,
            parameters[7]
        )
        slave.setState(Wait_CfgState())

    def setParameters(self, slave, wd_on: bool, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        if wd_on:    
            slave.wd_limit = watchdog_ms
            slave.watchdog = TimeLimitMilliseconds(watchdog_ms)
        else:
            slave.wd_limit = -1
        slave.slave_reaction_time = slave_reaction_time
        slave.reaction_timer = TimeLimitMilliseconds(slave_reaction_time)
        slave.freeze_mode_enable = freeze_mode_enable
        slave.locked = locked
        slave.group = group
        slave.master_add = master_add
        slave.id = id
            
    def setAddress(self, slave, address):
        raise SlaveException("Slave " + str(slave.getId) + " is in Wait Parameterization state, can't accept address setting telegram!")
    
    def checkTelegramToSend(self, slave, telegram):
        """"""
    
    