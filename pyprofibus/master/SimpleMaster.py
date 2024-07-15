# This master doesn't all the features of a real profibus master.
# It doesn't manage the slave configuration phase, assuming the slave are already dinamically
# parameterized as it expects
# It doesn't manage any diagnostic communication
# It manages data exchange communication
# It manages clear and fail safe mode, through global control frames too

import collections
import time
from pyprofibus.dp.dp import DpError, DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req, DpTelegram_GlobalControl, DpTelegram_SetPrm_Req
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.master.dp_master import DpMaster, DpSlaveState
from pyprofibus.util import ProfibusError, monotonic_time

class SimpleMaster(DpMaster):
    
    def __init__(self, dpmClass, phy, masterAddr, debug=False):
        super().__init__(dpmClass, phy, masterAddr, debug)
        self._slaveStateHandlers = {
		    DpSlaveState.STATE_INIT		: self._runSlave_init,
		    DpSlaveState.STATE_WDIAG	: self._runSlave_waitDiag,
		    DpSlaveState.STATE_WPRM		: self._runSlave_waitPrm,
		    DpSlaveState.STATE_WCFG		: self._runSlave_waitCfg,
		    DpSlaveState.STATE_WDXRDY	: self._runSlave_waitDxRdy,
		    DpSlaveState.STATE_DX		: self._runSlave_dataExchange,
            DpSlaveState.STATE_INVALID  : self._runSlave_invalid
    	}   
        self.clear_mode = False
        self.have_error_pool = []
        self.waiting_re_conf = []
        
    
    # This method adds a slave in all the data structures used by
    # the DpMaster, and also sets its state. In this class, after 
    # executing the parent method, we directly set the state of the slave
    # to data exchange, so that the master will consider it already parameterized
    
    def addSlave(self, slaveDesc, time_limit):
        super().addSlave(slaveDesc)
        slave = self._slaveStates[slaveDesc.slaveAddr]
        slave.setState(slave.STATE_DX, time_limit)
        slave.applyState()
        
    
    # This method manages well the data exchange communication between master and slave, 
    # considering in receiving both the cases of standard data ex telegram, and diagnostic request
    # from the slave, that can be used when the slave's watchdog expires
    # Unfortunately the error management is weak and doesn't trigger the clear mode when the slave 
    # is not answering (just inc a counter). So I duplicated the code of the parent method here, and 
    # modified to add a proper error management and clear mode, sending a multicast telegram
    # to all the slave so that they will switch to safe state 
    
    def _runSlave_dataExchange(self, parent, slave):
        dataExInData = None

        if slave.stateJustEntered():
            self._debugMsg("%sRunning Data_Exchange with slave %d..." % (
                "" if slave.dxCycleRunning else "Initialization finished. ",
                slave.slaveDesc.slaveAddr))
            slave.flushRxQueue()
            slave.faultDeb.ok()
            slave.dxStartTime = monotonic_time()
            slave.dxCycleRunning = True
            slave.dxCount = 0

        slaveOutputSize = slave.slaveDesc.outputSize
        if slave.pendingReq:
            for telegram in slave.getRxQueue():
                if slaveOutputSize == 0:
                    # This slave should not send any data.
                    self._debugMsg("Ignoring telegram in "
                        "DataExchange with slave %d:\n%s" %(
                        slave.slaveDesc.slaveAddr, str(telegram)))
                    slave.faultDeb.fault()
                    continue
                else:
                    # This slave is supposed to send some data.
                    # Get it.
                    if not DpTelegram_DataExchange_Con.checkType(telegram):
                        self._debugMsg("Ignoring telegram in "
                            "DataExchange with slave %d:\n%s" %(
                            slave.slaveDesc.slaveAddr, str(telegram)))
                        slave.faultDeb.fault()
                        continue
                    resFunc = telegram.fc & FdlTelegram.FC_RESFUNC_MASK
                    if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                        self._debugMsg("Slave %d requested diagnostics." %\
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
                    self._debugMsg("Data_Exchange timeout with slave %d" % (
                            slave.slaveDesc.slaveAddr))
                    #slave.faultDeb.fault()
                    #********** start new code **********#
                    self.have_error_pool.append(slave.slaveDesc.slaveAddr)
                    if self.clear_mode is not True:
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
                        self._debugMsg("Got data for slave, "
                                "but slave does not expect any input data.")
                    else:
                        ok = self._send(slave,
                                     telegram=DpTelegram_DataExchange_Req(
                                        da=slave.slaveDesc.slaveAddr,
                                        sa=self.masterAddr,
                                        du=toSlaveData),
                                     timeout=10)
                        if ok:
                            # We sent it. Reset the data.
                            slave.toSlaveData = None
                            slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                        else:
                            self._debugMsg("DataExchange_Req failed")
                            slave.faultDeb.fault()
        return dataExInData
    
    def goToClearMode(self):
        slave = self._slaveStates[FdlTelegram.ADDRESS_MCAST]
        globCtl = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
        				   sa = self.masterAddr)
        globCtl.controlCommand |= DpTelegram_GlobalControl.CCMD_CLEAR
        globCtl.groupSelect = 0x00 #all slaves
        print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
		 			% (globCtl.__class__, time.time(), globCtl))
        self.dpTrans.send(fcb = slave.fcb,
        		  telegram = globCtl)
        
        for s in self._DpMaster__slaveDescsList:
            slave_state = self._slaveStates[s.slaveAddr]
            if slave_state.getState() == slave_state.STATE_DX:
                slave_state.setState(slave_state.STATE_INVALID, -1)
        
        self.clear_mode = True
        # It is actually not necessary to manage the clear mode as a state of the master
        # because his behaviour will just be driven by the state of the slaves,
        # in fact the master in this mode will just communicate 0s to the slaves
        # in data exchange mode (see _runSlave_invalid) or try to reparameterize
        # the slaves that created problems
                
    
    # Since we are now managing the clear mode and fail safe state for the slaves,
    # we need to add the handler for the state STATE_INVALID, the only missing in 
    # the parent code, and this is done in the __init__ method of this class.
    # This method is the handler for the communication when a slave is in fail safe mode,
    # that is just sending frames with payload = 0x00, 0x00, just if it was in the standard
    # data exchange state, and also receiving frames with payload = 0x00, 0x00 (this is not fixed in the standard)
    def _runSlave_invalid(self, parent, slave):
        dataExInData = self._run_invalid(slave)
        if dataExInData:
            for b in dataExInData:
                if b != '\x00':
                    self._debugMsg("Received %b data different from 0 from slave %d but master is in Clear Mode" % (b, slave.slaveDesc.slaveAddr))
                    raise ProfibusError("Received data different from 0 but master is in Clear Mode")
        if len(self.have_error_pool) == 0:
            self.exitClearMode()
        return dataExInData

    def _run_invalid(self, slave):
        dataExInData = None

        slaveOutputSize = slave.slaveDesc.outputSize
        if slave.pendingReq:
            for telegram in slave.getRxQueue():
                if slaveOutputSize == 0:
                    # This slave should not send any data.
                    self._debugMsg("Ignoring telegram in "
                                     "DataExchange with slave %d:\n%s" % (
                                         slave.slaveDesc.slaveAddr, str(telegram)))
                    slave.faultDeb.fault()
                    continue
                else:
                    # This slave is supposed to send some data.
                    # Get it.

                    # CASE: the slave is working properly
                    if slave.slaveDesc.slaveAddr not in self.have_error_pool:
                        if not DpTelegram_DataExchange_Con.checkType(telegram):
                            self._debugMsg("Ignoring telegram in "
                                             "DataExchange with slave %d:\n%s" % (
                                                 slave.slaveDesc.slaveAddr, str(telegram)))
                            slave.faultDeb.fault()
                            continue
                        resFunc = telegram.fc & FdlTelegram.FC_RESFUNC_MASK
                        if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                            self._debugMsg("Slave %d requested diagnostics." %
                                             slave.slaveDesc.slaveAddr)
                            slave.setState(slave.STATE_WDXRDY, 0.2)
                        elif resFunc == FdlTelegram.FC_RS:
                            raise DpError("Service not active "
                                          "on slave %d" % slave.slaveDesc.slaveAddr)
                        dataExInData = telegram.getDU()
                    ##CASE: broken slave, check if answered the set prm request
                    #else:
                    #    if slave.shortAckReceived():
                    #        self.have_error_pool.remove(slave.slaveDesc.slaveAddr)
                    #        slave.setState(slave.STATE_WCFG)
            if slave.slaveDesc.slaveAddr in self.have_error_pool:
                self._repairSlaveRoutine(slave)
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
                    self._debugMsg("Re-parameterization timeout with slave %d" % (
                            slave.slaveDesc.slaveAddr))
                    slave.pendingReq = None
            
        else:
            diagPeriod = slave.slaveDesc.diagPeriod
            if diagPeriod > 0 and slave.dxCount >= diagPeriod:
                # The input-only slave shall periodically be diagnosed.
                # Go to diagnostic state.
                slave.setState(slave.STATE_WDXRDY, 0.2)
            else:
                # Send the out data telegram with payload = 0x00, 0x00.
                if slave.slaveDesc.inputSize == 0:
                    self._debugMsg("This slave does not expect any data")
                else:
                    if slave.slaveDesc.slaveAddr not in self.have_error_pool:
                        # slave working properly
                        ok = self._send(slave,
                                         telegram=DpTelegram_DataExchange_Req(
                                             da=slave.slaveDesc.slaveAddr,
                                             sa=self.masterAddr,
                                             du=bytearray((0x00, 0x00))),
                                         timeout=10)
                    else:
                        # broken slave, try to reparameterize
                        param_tg = slave.slaveDesc.setPrmTelegram
                        param_tg.sa = self.masterAddr
                        ok = self._send(slave,
                                        telegram=param_tg,
                                        timeout=10)
                    if ok:
                        # We sent it. Reset the data.
                        slave.toSlaveData = None
                        slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                    else:
                        self._debugMsg("DataExchange_Req failed")
                        slave.faultDeb.fault()
        return dataExInData
    
    def _repairSlaveRoutine(self, slave):
        if slave.shortAckReceived:
            if slave.slaveDesc.slaveAddr not in self.waiting_re_conf:
                self.waiting_re_conf.append(slave.slaveDesc.slaveAddr)
                self._debugMsg("XXX| Slave %d has been reparameterized!" % slave.slaveDesc.slaveAddr)
                slave.slaveDesc.chkCfgTelegram.sa = self.masterAddr
                ok = self._send(slave,
                        telegram=slave.slaveDesc.chkCfgTelegram,
                        timeout=10)
                self.phy.discard()
                if not ok:
                    self._debugMsg("Couldn't send reconfiguration telegram")
            elif slave.slaveDesc.slaveAddr in self.waiting_re_conf:
                self._debugMsg("XXX| Slave %d has been reconfigured and is back to work!"
                           % slave.slaveDesc.slaveAddr)
                self.waiting_re_conf.remove(slave.slaveDesc.slaveAddr)
                self.have_error_pool.remove(slave.slaveDesc.slaveAddr)
                slave.setState(slave.STATE_DX, 100)
                slave.applyState()
            else:
                raise ProfibusError("Something went wrong!")
         
    
    # This method is called when all the slaves are working correctly, after the master
    # going to Clear Mode. All the slaves are switched back to the data exchange state,
    # except the one that was broken, that stays in the wait for configuration state.
    # A global telegram is sent to communicate to all the slaves
    # that the master is back to Operational Mode. 
    def exitClearMode(self):
        slave = self._slaveStates[FdlTelegram.ADDRESS_MCAST]
        globCtl = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
        				   sa = self.masterAddr)
        globCtl.controlCommand |= DpTelegram_GlobalControl.CCMD_OPERATE
        globCtl.groupSelect = 0x00 #all slaves
        print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
		 			% (globCtl.__class__, time.time(), globCtl))
        self.dpTrans.send(fcb = slave.fcb,
        		  telegram = globCtl)
        #just to clean
        #print("CLEANING")
        #time.sleep(0.5)
        #self._pollRx()
        
        for s in self._DpMaster__slaveDescsList:
            slave_state = self._slaveStates[s.slaveAddr]
            if slave_state.getState() == slave_state.STATE_DX:
                continue
            if slave_state.getState() != slave_state.STATE_INVALID:
                self._debugMsg("""Slave %d was expected to be in fail safe state
                                or waiting for re-configuration
                                 but was not (ignoring)""" % (s.slaveAddr))
                continue
            slave_state.setState(slave.STATE_DX, 100)
        
        self.clear_mode = False

    def _runSlave(self, slave):
        self._pollRx()
        
        if slave.stateHasTimeout():
            self._debugMsg("State machine timeout! "
			    "Trying to re-initializing slave %d..." %\
			    slave.slaveDesc.slaveAddr)
            slave.setState(slave.STATE_INVALID)
            self.have_error_pool.append(slave.slaveDesc.slaveAddr)
            dataExInData = None
        else:
            handler = self._slaveStateHandlers[slave.getState()]
            dataExInData = handler(self, slave)

            if slave.stateIsChanging():
                self._debugMsg("slave[%02X].state --> '%s'" % (
                    slave.slaveDesc.slaveAddr,
                    slave.state2name[slave.getNextState()]))
        slave.applyState()

        return dataExInData

    def getSlaveStates(self):
        return self._slaveStates