# This master doesn't all the features of a real profibus master.
# It doesn't manage the slave configuration phase, assuming the slave are already dinamically
# parameterized as it expects
# It doesn't manage any diagnostic communication
# It manages data exchange communication
# It manages clear and fail safe mode, through global control frames too

import collections
from pyprofibus.dp.dp import DpError, DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req, DpTelegram_GlobalControl
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.master.dp_master import DpMaster, DpSlaveState

class SimpleMaster(DpMaster):
    
    def __init__(self, dpmClass, phy, masterAddr, debug=False):
        super().__init__(dpmClass, phy, masterAddr, debug)
        self.__slaveStateHandlers = collections.ChainMap(
            self.__slaveStateHandlers,
            {DpSlaveState._STATE_INVALID: self.__runSlave_invalid}
        )
        self.clear_mode = False
        
    
    # This method adds a slave in all the data structures used by
    # the DpMaster, and also sets its state. In this class, after 
    # executing the parent method, we directly set the state of the slave
    # to data exchange, so that the master will consider it already parameterized
    
    def addSlave(self, slaveDesc, time_limit):
        super().addSlave(slaveDesc)
        slave = self.__slaveStates[slaveDesc.slaveAddr]
        slave.setState(slave.STATE_DX, time_limit)
        slave.applyState()
        
    
    # This method manages well the data exchange communication between master and slave, 
    # considering in receiving both the cases of standard data ex telegram, and diagnostic request
    # from the slave, that can be used when the slave's watchdog expires
    # Unfortunately the error management is weak and doesn't trigger the clear mode when the slave 
    # is not answering (just inc a counter). So I duplicated the code of the parent method here, and 
    # modified to add a proper error management and clear mode, sending a multicast telegram
    # to all the slave so that they will switch to safe state 
    
    def __runSlave_dataExchange(self, slave):
        dataExInData = None

        if slave.stateJustEntered():
            self.__debugMsg("%sRunning Data_Exchange with slave %d..." % (
                "" if slave.dxCycleRunning else "Initialization finished. ",
                slave.slaveDesc.slaveAddr))
            slave.flushRxQueue()
            slave.faultDeb.ok()
            slave.dxStartTime = super().monotonic_time()
            slave.dxCycleRunning = True
            slave.dxCount = 0

        slaveOutputSize = slave.slaveDesc.outputSize
        if slave.pendingReq:
            for telegram in slave.getRxQueue():
                if slaveOutputSize == 0:
                    # This slave should not send any data.
                    self.__debugMsg("Ignoring telegram in "
                        "DataExchange with slave %d:\n%s" %(
                        slave.slaveDesc.slaveAddr, str(telegram)))
                    slave.faultDeb.fault()
                    continue
                else:
                    # This slave is supposed to send some data.
                    # Get it.
                    if not DpTelegram_DataExchange_Con.checkType(telegram):
                        self.__debugMsg("Ignoring telegram in "
                            "DataExchange with slave %d:\n%s" %(
                            slave.slaveDesc.slaveAddr, str(telegram)))
                        slave.faultDeb.fault()
                        continue
                    resFunc = telegram.fc & FdlTelegram.FC_RESFUNC_MASK
                    if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                        self.__debugMsg("Slave %d requested diagnostics." %\
                            slave.slaveDesc.slaveAddr)
                        slave.setState(slave.STATE_WDXRDY, 0.2)
                    elif resFunc == FdlTelegram.FC_RS:
                        raise DpError("Service not active "
                            "on slave %d" % slave.slaveDesc.slaveAddr)
                    dataExInData = telegram.getDU()
            if (dataExInData is not None or
                (slaveOutputSize == 0 and slave.shortAckReceived)):
                # We received some data or an ACK (input-only slave).
                slave.pendingReq = None
                slave.faultDeb.ok()
                slave.restartStateTimeout()
                self._releaseSlave(slave)
            else:
                # No data or ACK received from slave.
                if slave.pendingReqTimeout.exceed():
                    self.__debugMsg("Data_Exchange timeout with slave %d" % (
                            slave.slaveDesc.slaveAddr))
                    #slave.faultDeb.fault()
                    #********** start new code **********#
                    self.goToClearMode()
                    #********** end new code **********#
                    slave.pendingReq = None
        else:
            diagPeriod = slave.slaveDesc.diagPeriod
            if diagPeriod > 0 and slave.dxCount >= diagPeriod:
                # The input-only slave shall periodically be diagnosed.
                # Go to diagnostic state.
                slave.setState(slave.STATE_WDXRDY, 0.2)
            else:
                # Send the out data telegram, if any.
                toSlaveData = slave.toSlaveData
                if toSlaveData is not None:
                    if slave.slaveDesc.inputSize == 0:
                        self.__debugMsg("Got data for slave, "
                                "but slave does not expect any input data.")
                    else:
                        ok = self.__send(slave,
                                     telegram=DpTelegram_DataExchange_Req(
                                        da=slave.slaveDesc.slaveAddr,
                                        sa=self.masterAddr,
                                        du=toSlaveData),
                                     timeout=0.1)
                        if ok:
                            # We sent it. Reset the data.
                            slave.toSlaveData = None
                            slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                        else:
                            self.__debugMsg("DataExchange_Req failed")
                            slave.faultDeb.fault()
        if self.__checkFaultDeb(slave, True):
            return None
        return dataExInData
    
    def goToClearMode(self):
        slave = self.__slaveStates[FdlTelegram.ADDRESS_MCAST]
        globCtl = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
        				   sa = self.masterAddr)
        globCtl.controlCommand |= DpTelegram_GlobalControl.CCMD_CLEAR
        globCtl.groupSelect = 0x00 #all slaves
        self.dpTrans.send(fcb = slave.fcb,
        		  telegram = globCtl)
        
        for s in self.__slaveDescsList:
            slave_state = self.__slaveStates[s.slaveAddr]
            if slave_state.getState() == slave_state.STATE_DX:
                slave_state.setState(slave_state._STATE_INVALID, -1)
        
        self.clear_mode = True
        # It is actually not necessary to manage the clear mode as a state of the master
        # because his behaviour will just be driven by the state of the slaves,
        # in fact the master in this mode will just communicate 0s to the slaves
        # in data exchange mode (see __runSlave_invalid) or try to reparameterize
        # the slaves that created problems
                
    
    # Since we are now managing the clear mode and fail safe state for the slaves,
    # we need to add the handler for the state _STATE_INVALID, the only missing in 
    # the parent code, and this is done in the __init__ method of this class.
    # This method is the handler for the communication when a slave is in fail safe mode,
    # that is just sending frames with no payload, just if it was in the standard
    # data exchange state, and also receiving frames with no payload (this is not fixed in the standard)
    def __runSlave_invalid(self, slave):
        slaveOutputSize = slave.slaveDesc.outputSize
        if slave.pendingReq:
            for telegram in slave.getRxQueue():
                if slaveOutputSize == 0:
                    # This slave should not send any data.
                    self.__debugMsg("Ignoring telegram in "
                                     "DataExchange with slave %d:\n%s" % (
                                         slave.slaveDesc.slaveAddr, str(telegram)))
                    slave.faultDeb.fault()
                    continue
                else:
                    # This slave is supposed to send some data.
                    # Get it.
                    if not DpTelegram_DataExchange_Con.checkType(telegram):
                        self.__debugMsg("Ignoring telegram in "
                                         "DataExchange with slave %d:\n%s" % (
                                             slave.slaveDesc.slaveAddr, str(telegram)))
                        slave.faultDeb.fault()
                        continue
                    resFunc = telegram.fc & FdlTelegram.FC_RESFUNC_MASK
                    if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                        self.__debugMsg("Slave %d requested diagnostics." %
                                         slave.slaveDesc.slaveAddr)
                        slave.setState(slave.STATE_WDXRDY, 0.2)
                    elif resFunc == FdlTelegram.FC_RS:
                        raise DpError("Service not active "
                                      "on slave %d" % slave.slaveDesc.slaveAddr)
                    #********************#
                    if telegram.getDU() is not None:
                        raise DpError("Received data from slave while in fail safe mode!")
                    #********************#
                    dataExInData = telegram.getDU()
            # We received some data or an ACK (input-only slave).
            slave.pendingReq = None
            slave.faultDeb.ok()
            slave.restartStateTimeout()
            self._releaseSlave(slave)
        else:
            diagPeriod = slave.slaveDesc.diagPeriod
            if diagPeriod > 0 and slave.dxCount >= diagPeriod:
                # The input-only slave shall periodically be diagnosed.
                # Go to diagnostic state.
                slave.setState(slave.STATE_WDXRDY, 0.2)
            else:
                # Send the out data telegram with no payload.
                if slave.slaveDesc.inputSize == 0:
                    self.__debugMsg("This slave does not expect any data")
                else:
                    ok = self.__send(slave,
                                     telegram=DpTelegram_DataExchange_Req(
                                         da=slave.slaveDesc.slaveAddr,
                                         sa=self.masterAddr,
                                         du=None),
                                     timeout=0.1)
                    if ok:
                        # We sent it. Reset the data.
                        slave.toSlaveData = None
                        slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                    else:
                        self.__debugMsg("DataExchange_Req failed")
                        slave.faultDeb.fault()
        if self.__checkFaultDeb(slave, True):
            return None
        return dataExInData


        
