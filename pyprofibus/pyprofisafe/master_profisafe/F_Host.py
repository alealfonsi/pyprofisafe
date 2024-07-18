import time
from pyprofibus.dp.dp import DpError, DpTelegram_DataExchange_Con, DpTelegram_DataExchange_Req, DpTelegram_GlobalControl
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram, FdlTelegram_ack
from pyprofibus.master.SimpleMaster import SimpleMaster
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteHost import ControlByteHost
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTransceiver import ProfiSafeTransceiver
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_GlobalControl import ProfiSafeTelegram_GlobalControl
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Req import ProfiSafeTelegram_Req
from pyprofibus.util import ProfibusError, monotonic_time
from inputimeout import inputimeout, TimeoutOccurred


class F_Host(SimpleMaster):

    def __init__(self, dpmClass, phy, masterAddr, debug=False):
        super().__init__(dpmClass, phy, masterAddr, debug)
        self.ps_trans = ProfiSafeTransceiver(self.dpTrans)
        self._slaveStates = super().getSlaveStates()
    
    def _send(self, slave, telegram, timeout):
        """Asynchronously send a telegram to a slave.
        """
        slave.pendingReq = telegram
        slave.shortAckReceived = False
        try:
            transceiver = self.ps_trans
            print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
                    % (telegram.__class__, time.time(), telegram.payload))
            transceiver.send(telegram)
        except (ProfibusError, ProfiSafeError) as e:
            slave.pendingReq = None
            self._debugMsg(str(e))
            return False
        slave.pendingReqTimeout.start(timeout)
        return True
    
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
                                   "DataExchange with slave %d:\n%s" % (
                                       slave.slaveDesc.slaveAddr, str(telegram)))
                    slave.faultDeb.fault()
                    continue
                else:
                    # This slave is supposed to send some data.
                    # Get it.
                    if not DpTelegram_DataExchange_Con.checkType(telegram.payload):
                        self._debugMsg("Ignoring telegram in "
                                       "DataExchange with slave %d:\n%s" % (
                                           slave.slaveDesc.slaveAddr, str(telegram)))
                        slave.faultDeb.fault()
                        continue
                    resFunc = telegram.payload.fc & FdlTelegram.FC_RESFUNC_MASK
                    if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                        self._debugMsg("Slave %d requested diagnostics." %
                                       slave.slaveDesc.slaveAddr)
                        slave.setState(slave.STATE_WDXRDY, 0.2)
                    elif resFunc == FdlTelegram.FC_RS:
                        raise DpError("Service not active "
                                       "on slave %d" % slave.slaveDesc.slaveAddr)
                    dataExInData = telegram.payload.getDU()
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
                    self.have_error_pool.append(slave.slaveDesc.slaveAddr)
                    if self.clear_mode is not True:
                        self.goToClearMode()
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
                        payload = DpTelegram_DataExchange_Req(
                            da=slave.slaveDesc.slaveAddr,
                            sa=self.masterAddr,
                            du=toSlaveData)
                        control_byte = ControlByteHost.TOGGLE_H + ControlByteHost.LOOPBACK
                        crc = b'\xab' * 3
                        ok = self._send(slave,
                                     telegram=ProfiSafeTelegram_Req(payload, control_byte, crc),
                                     timeout=100)
                        if ok:
                            # We sent it. Reset the data.
                            slave.toSlaveData = None
                            slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                        else:
                            self._debugMsg("DataExchange_Req failed")
                            slave.faultDeb.fault()
        return dataExInData 

    def _pollRx(self):
        try:
            ok, telegram = self.ps_trans.poll()
        except (ProfibusError, ProfiSafeError) as e:
            self._debugMsg("RX error: %s" % str(e))
            return

        if ok and telegram:
            print("XXX| Master received frame of type %s at time: %d\nXXX| %s" 
                  % (telegram.__class__, time.time(), telegram.payload))
            if telegram.payload.da == self.masterAddr:
                if telegram.payload.sa in self._slaveStates:
                    slave = self._slaveStates[telegram.payload.sa]
                    slave.rxQueue.append(telegram)
                    slave.fcb.handleReply()
                else:
                    self._debugMsg("XXX| Master received telegram from "
                                   "unknown station %d at time: %d\nXXX| %s" %(
                                   telegram.sa, time.time(), telegram))
            else:
                self._debugMsg("Received telegram for "
                              "foreign station:\n%s" % str(telegram))
        else:
            if telegram:
                self._debugMsg("XXX| Master received corrupt "
                              "telegram at time: %d\nXXX| %s" % (time.time(), telegram))

    def goToClearMode(self):
        slave = self._slaveStates[FdlTelegram.ADDRESS_MCAST]
        payload = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
        				   sa = self.masterAddr)
        payload.controlCommand |= DpTelegram_GlobalControl.CCMD_CLEAR
        payload.groupSelect = 0x00 #all slaves
        globCtl = ProfiSafeTelegram_GlobalControl(
            payload,
            ControlByteHost.OPERATOR_ACK_REQUESTED +
            ControlByteHost.ACTIVATE_FV +
            ControlByteHost.LOOPBACK,
            b'\xab' * 3)
        print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
		 			% (globCtl.__class__, time.time(), globCtl.payload))
        self.ps_trans.send(telegram = globCtl)
        
        for s in self._DpMaster__slaveDescsList:
            slave_state = self._slaveStates[s.slaveAddr]
            if slave_state.getState() == slave_state.STATE_DX:
                slave_state.setState(slave_state.STATE_INVALID, -1)
        
        self.clear_mode = True

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
                        if not DpTelegram_DataExchange_Con.checkType(telegram.payload):
                            self._debugMsg("Ignoring telegram in "
                                             "DataExchange with slave %d:\n%s" % (
                                                 slave.slaveDesc.slaveAddr, str(telegram)))
                            slave.faultDeb.fault()
                            continue
                        resFunc = telegram.payload.fc & FdlTelegram.FC_RESFUNC_MASK
                        if resFunc in (FdlTelegram.FC_DH, FdlTelegram.FC_RDH):
                            self._debugMsg("Slave %d requested diagnostics." %
                                             slave.slaveDesc.slaveAddr)
                            slave.setState(slave.STATE_WDXRDY, 0.2)
                        elif resFunc == FdlTelegram.FC_RS:
                            raise DpError("Service not active "
                                          "on slave %d" % slave.slaveDesc.slaveAddr)
                        dataExInData = telegram.payload.getDU()
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
                    self._debugMsg("Timeout with slave %d while in clear mode" % (
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
                        payload = DpTelegram_DataExchange_Req(
                                             da=slave.slaveDesc.slaveAddr,
                                             sa=self.masterAddr,
                                             du=bytearray((0x00, 0x00)))
                        control_byte = (ControlByteHost.OPERATOR_ACK_REQUESTED +
                            ControlByteHost.ACTIVATE_FV +
                            ControlByteHost.LOOPBACK)
                        crc = b'\xab' * 3
                        ok = self._send(slave,
                                         telegram=ProfiSafeTelegram_Req(payload, control_byte, crc),
                                         timeout=10)
                    else:
                        # broken slave, ask for ack to the operator
                        ok = False
                        try:
                            inputimeout(prompt="Press ENTER to give ack for slave reintegration...", timeout=5)
                            print("Ack received, slave reintegration...")
                            self.slaveReintegration(slave)
                        except TimeoutOccurred:
                            print("No ack received, continuing cyclic communication")
                    if ok:
                        # We sent it. Reset the data.
                        slave.toSlaveData = None
                        slave.dxCount = min(slave.dxCount + 1, 0x3FFFFFFF)
                    else:
                        self._debugMsg("DataExchange_Req failed")
                        slave.faultDeb.fault()
        return dataExInData

    def slaveReintegration(self, slave):
        self.have_error_pool.remove(slave.slaveDesc.slaveAddr)
        slave.setState(slave.STATE_DX, 100)
        slave.applyState()
    
    def exitClearMode(self):
        slave = self._slaveStates[FdlTelegram.ADDRESS_MCAST]
        payload = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
        				   sa = self.masterAddr)
        payload.controlCommand |= DpTelegram_GlobalControl.CCMD_OPERATE
        payload.groupSelect = 0x00 #all slaves
        control_byte = ControlByteHost(
            ControlByteHost.OPERATOR_ACK +
            ControlByteHost.LOOPBACK
        )
        crc = b'\xab' * 3
        globCtl = ProfiSafeTelegram_GlobalControl(payload, control_byte, crc)
        print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
		 			% (globCtl.__class__, time.time(), globCtl.payload))
        self.ps_trans.send(telegram = globCtl)
        
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