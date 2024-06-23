from pyprofibus.dp.dp import DpTelegram_ChkCfg_Req, DpTelegram_SetPrm_Req
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram, FdlTelegram_ack
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.SlaveState import SlaveState
from pyprofibus.util import TimeLimit, TimeLimitMilliseconds

class Wait_CfgState(SlaveState):
    
    _self = None
    
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def checkTelegram(self, slave, telegram):
        if DpTelegram_ChkCfg_Req.checkType(telegram):
            conf = telegram.getDU()
            if self.__checkConfiguration(conf):
                self.sendResponse(slave)
                slave.setState(Data_ExchState())
            else:
                raise SlaveException("""Slave %d: the configuration received is wrong!
                                     Telegram: %s""" % (slave.getId(), telegram))
            
        elif DpTelegram_SetPrm_Req.checkType(telegram):
            print("SetPrm request received while in ChkCfg State")
            """TO-DO"""
        
        else:
            raise SlaveException("""Slave %s is waiting for configuration check but received 
                                 telegram: %s""" % (str(slave.getId()), telegram))

    def __checkConfiguration(self, conf):
        
        """TO-DO"""
        return True
    
    def sendResponse(self, slave):
        send_telegram = FdlTelegram_ack()
        send_telegram.da = slave.master_add
        send_telegram.sa = slave.getAddress()
        send_telegram.fc = FdlTelegram.FC_OK
        slave.send(send_telegram)

    def setParameters(self, slave, wd_on, watchdog_ms: int, slave_reaction_time, freeze_mode_enable, locked, group, master_add, id):
        if wd_on:    
            slave.wd_limit = watchdog_ms
        else:
            slave.wd_limit = -1
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
        if not FdlTelegram_ack.checkType(telegram):
            raise SlaveException()
        return True    