# -*- coding: utf-8 -*-
#
# PROFIBUS DP - Master
#
# Copyright (c) 2013-2021 Michael Buesch <m@bues.ch>
#
# Licensed under the terms of the GNU General Public License version 2,
# or (at your option) any later version.
#

from __future__ import division, absolute_import, print_function, unicode_literals
import time
from pyprofibus.compat import *

from pyprofibus.fieldbus_data_link.fdl import *
from pyprofibus.dp.dp import *
from pyprofibus.master.DpMasterInterface import DpMasterInterface
from pyprofibus.master.DpSlaveDescInterface import DpSlaveDescInterface
from pyprofibus.master.DpSlaveStateInterface import DpSlaveStateInterface
from pyprofibus.util import *

import gc
import math

__all__ = [
	"DpSlaveDesc",
	"DPM1",
	"DPM2",
]

class DpSlaveState(DpSlaveStateInterface):
	"""Run time state of a DP slave that is managed by a DPM instance.
	"""

	STATE_INVALID	= -1
	STATE_INIT	= 0 # Initialize
	STATE_WDIAG	= 1 # Wait for diagnosis
	STATE_WPRM	= 2 # Wait for Prm telegram
	STATE_WCFG	= 3 # Wait for Cfg telegram
	STATE_WDXRDY	= 4 # Wait for Data_Exchange ready
	STATE_DX	= 5 # Data_Exchange

	state2name = {
		STATE_INVALID	: "Invalid",
		STATE_INIT	: "Init",
		STATE_WDIAG	: "Wait for diag",
		STATE_WPRM	: "Wait for Prm",
		STATE_WCFG	: "Wait for Cfg",
		STATE_WDXRDY	: "Request diag and wait for DX-ready",
		STATE_DX	: "Data_Exchange",
	}

	# State timeouts in seconds
	stateTimeLimits = {
		STATE_INVALID	: TimeLimit.UNLIMITED,
		STATE_INIT		: TimeLimit.UNLIMITED,
		STATE_WDIAG		: TimeLimit.UNLIMITED, #1.0,
		STATE_WPRM		: TimeLimit.UNLIMITED, #10,
		STATE_WCFG		: TimeLimit.UNLIMITED, #0.5,
		STATE_WDXRDY	: TimeLimit.UNLIMITED, #1.0,
		STATE_DX		: TimeLimit.UNLIMITED, #0.5,
	}

	__slots__ = (
		"__nextState",
		"__prevState",
		"__state",
		"__stateTimeout",
		"dxStartTime",
		"dxCount",
		"dxCycleRunning",
		"faultDeb",
		"fcb",
		"master",
		"fromSlaveData",
		"toSlaveData",
		"pendingReq",
		"pendingReqTimeout",
		"rxQueue",
		"shortAckReceived",
		"slaveDesc",
	)

	def __init__(self, master, slaveDesc):
		self.master = master
		self.slaveDesc = slaveDesc

		# Fault counter
		self.faultDeb = FaultDebouncer()

		self.__state = self.STATE_INVALID
		self.__nextState = self.STATE_INVALID
		self.__prevState = self.STATE_INVALID
		self.__stateTimeout = TimeLimit()

		# Context for FC-Bit toggeling
		self.fcb = FdlFCB()
		
		self.setState(self.STATE_INIT)
		self.applyState()

		# Currently running request telegram
		self.pendingReq = None
		self.pendingReqTimeout = TimeLimit()
		self.shortAckReceived = False

		# Data_Exchange context
		self.dxStartTime = 0.0
		self.dxCount = 0

		# Received telegrams
		self.rxQueue = []

		# In/Out user data
		self.toSlaveData = None
		self.fromSlaveData = None

	def getRxQueue(self):
		rxQueue = self.rxQueue
		self.rxQueue = []
		return rxQueue

	def flushRxQueue(self):
		self.rxQueue = []

	def getState(self):
		return self.__state

	def getNextState(self):
		return self.__nextState

	def setState(self, state, stateTimeLimit=None):
		if stateTimeLimit is None:
			stateTimeLimit = self.stateTimeLimits[state]
		if state == self.STATE_INIT:
			self.dxCycleRunning = False
			self.fcb.resetFCB()
		self.__nextState = state
		self.__stateTimeout.start(stateTimeLimit)
		self.master.phy.clearTxQueueAddr(self.slaveDesc.slaveAddr)
		self.master._releaseSlave(self)

	def applyState(self):
		# Enter the new state
		self.__prevState, self.__state = self.__state, self.__nextState

		# Handle state switch
		if self.stateJustEntered():
			self.pendingReq = None

	def stateJustEntered(self):
		# Returns True, if the state was just entered.
		return self.__prevState != self.__state

	def stateIsChanging(self):
		# Returns True, if the state was just changed.
		return self.__nextState != self.__state

	def restartStateTimeout(self, timeout = None):
		self.__stateTimeout.start(timeout)

	def stateHasTimeout(self):
		return self.__stateTimeout.exceed()

class DpSlaveDesc(DpSlaveDescInterface):
	"""Static descriptor data of a DP slave that
	is managed by a DPM instance.
	"""

	__slots__ = (
		"dpm",
		"gsd",
		"slaveAddr",
		"identNumber",
		"name",
		"index",
		"inputSize",
		"outputSize",
		"diagPeriod",
		"slaveConf",
		"userData",
		"setPrmTelegram",
		"chkCfgTelegram",
	)

	def __init__(self, slaveConf=None):
		self.dpm = None
		self.gsd = slaveConf.gsd if slaveConf else None
		self.slaveAddr = slaveConf.addr if slaveConf else None
		self.identNumber = self.gsd.getIdentNumber() if self.gsd else 0
		self.name = slaveConf.name if slaveConf else None
		self.index = slaveConf.index if slaveConf else None
		self.inputSize = slaveConf.inputSize if slaveConf else 0
		self.outputSize = slaveConf.outputSize if slaveConf else 0
		self.diagPeriod = slaveConf.diagPeriod if slaveConf else 0
		self.slaveConf = slaveConf
		self.userData = {} # For use by application code.

		# Prepare a Set_Prm telegram.
		self.setPrmTelegram = DpTelegram_SetPrm_Req(
					da=self.slaveAddr,
					sa=None)
		self.setPrmTelegram.identNumber = self.identNumber

		# Prepare a Chk_Cfg telegram.
		self.chkCfgTelegram = DpTelegram_ChkCfg_Req(
					da=self.slaveAddr,
					sa=None)

	def setCfgDataElements(self, cfgDataElements):
		"""Sets DpCfgDataElement()s from the specified list
		in the Chk_Cfg telegram.
		"""
		if cfgDataElements is not None:
			self.chkCfgTelegram.clearCfgDataElements()
			for cfgDataElement in cfgDataElements:
				self.chkCfgTelegram.addCfgDataElement(cfgDataElement)

	def setUserPrmData(self, userPrmData):
		"""Sets the User_Prm_Data of the Set_Prm telegram.
		"""
		if userPrmData is not None:
			self.setPrmTelegram.clearUserPrmData()
			self.setPrmTelegram.addUserPrmData(userPrmData)

	def setSyncMode(self, enabled):
		"""Enable/disable sync-mode.
		Must be called before parameterisation."""

		if enabled:
			self.setPrmTelegram.stationStatus |= DpTelegram_SetPrm_Req.STA_SYNC
		else:
			self.setPrmTelegram.stationStatus &= ~DpTelegram_SetPrm_Req.STA_SYNC

	def setFreezeMode(self, enabled):
		"""Enable/disable freeze-mode.
		Must be called before parameterisation."""

		if enabled:
			self.setPrmTelegram.stationStatus |= DpTelegram_SetPrm_Req.STA_FREEZE
		else:
			self.setPrmTelegram.stationStatus &= ~DpTelegram_SetPrm_Req.STA_FREEZE

	def setGroupMask(self, groupMask):
		"""Assign the slave to one or more groups.
		Must be called before parameterisation."""

		self.setPrmTelegram.groupIdent = groupMask

	def setWatchdog(self, timeoutMS):
		"""Set the watchdog timeout (in milliseconds).
		If timeoutMS is 0, the watchdog is disabled."""

		if timeoutMS <= 0:
			# Disable watchdog
			self.setPrmTelegram.stationStatus &= ~DpTelegram_SetPrm_Req.STA_WD
			return

		# Enable watchdog
		self.setPrmTelegram.stationStatus |= DpTelegram_SetPrm_Req.STA_WD

		# Set timeout factors
		fact1 = timeoutMS / 10
		fact2 = 1
		#while fact1 > 255:
		#	fact2 *= 2
		#	fact1 /= 2
		#	if fact2 > 255:
		#		raise DpError("Watchdog timeout %d is too big" % timeoutMS)
		#fact1 = min(255, int(math.ceil(fact1)))
		self.setPrmTelegram.wdFact1 = fact1
		self.setPrmTelegram.wdFact2 = fact2

	def setMasterOutData(self, data):
		"""Set the master-out-data that will be sent the
		next time we are able to send something to that slave.
		"""
		self.dpm._setToSlaveData(self, data)

	def getMasterInData(self):
		"""Get the latest received master-in-data.
		Returns None, if there was no received data.
		"""
		return self.dpm._getFromSlaveData(self)

	def setOutData(self, outData):
		"""Deprecated: Don't use this method. Use setMasterOutData() instead."""
		self.setMasterOutData(outData)

	def getInData(self):
		"""Deprecated: Don't use this method. Use getMasterInData() instead."""
		return self.getMasterInData()

	def isConnecting(self):
		"""Returns True, if the slave is in the process of getting connected/configured,
		but is not fully connected, yet.
		Otherwise returns False.
		"""
		return self.dpm._slaveIsConnecting(self)

	def isConnected(self):
		"""Returns True, if this slave is fully connected and Data_Exchange
		or periodic slave diagnosis is currently running.
		Otherwise returns False.
		"""
		return self.dpm._slaveIsConnected(self)

	def __repr__(self):
		return "DpSlaveDesc(identNumber=%s, slaveAddr=%d)" %\
			(intToHex(self.identNumber), self.slaveAddr)

class DpMaster(DpMasterInterface):
	__slots__ = (
		"__runTimer",
		"__runCount",
		"__haveToken",
		"__runNextSlaveIndex",
		"__slaveDescs",
		"__slaveDescsList",
		"_slaveStates",
		"__slowDown",
		"__slowDownFact",
		"__slowDownUntil",
		"debug",
		"dpTrans",
		"dpmClass",
		"fdlTrans",
		"masterAddr",
		"phy",
	)

	def __init__(self, dpmClass, phy, masterAddr, debug=False):
		self.dpmClass = dpmClass
		self.phy = phy
		self.masterAddr = masterAddr
		self.debug = debug

		self.__runTimer = monotonic_time()
		self.__runCount = 0

		# Create the transceivers
		self.fdlTrans = FdlTransceiver(self.phy)
		self.dpTrans = DpTransceiver(self.fdlTrans, thisIsMaster=True)

		mcastSlaveDesc = DpSlaveDesc()
		mcastSlaveDesc.slaveAddr = FdlTelegram.ADDRESS_MCAST
		mcastSlave = DpSlaveState(self, mcastSlaveDesc)

		self.__slaveDescs = {
			FdlTelegram.ADDRESS_MCAST : mcastSlaveDesc,
		}
		self._slaveStates = {
			FdlTelegram.ADDRESS_MCAST : mcastSlave,
		}
		self.__slaveDescsList = []
		self.__runNextSlaveIndex = 0

		# Do we have the token?
		self.__haveToken = True

		self.__slowDown = False
		self.__slowDownUntil = monotonic_time()
		self.__slowDownFact = 1

	def _debugMsg(self, msg):
		if self.debug:
			print("DPM%d: %s" % (self.dpmClass, msg))

	def __errorMsg(self, msg):
		print("DPM%d:  >ERROR<  %s" % (self.dpmClass, msg))

	def __masterSlowDown(self):
		"""A severe communication error occurred.
		Slow down the state machine a bit.
		"""
		self.__slowDown = True
		self.__slowDownUntil = monotonic_time() + (0.01 * self.__slowDownFact)
		self._debugMsg("Slow down factor = %d" % self.__slowDownFact)
		self.__slowDownFact = min(self.__slowDownFact + 1, 10)

	def destroy(self):
		if self.phy:
			self.phy.close()
			self.phy = None

	def addSlave(self, slaveDesc):
		"""Register a slave."""

		if slaveDesc.inputSize <= 0:
			raise DpError("Slave %d: input_size=0 is currently not supported." % (
				      slaveDesc.slaveAddr))

		slaveAddr = slaveDesc.slaveAddr
		if slaveAddr in self.__slaveDescs or\
		   slaveAddr in self._slaveStates:
			raise DpError("Slave %d is already registered." % slaveAddr)
		slaveDesc.dpm = self
		self.__slaveDescs[slaveAddr] = slaveDesc
		self._slaveStates[slaveAddr] = DpSlaveState(self, slaveDesc)

		# Rebuild the slave desc list.
		self.__slaveDescsList = [
			desc
			for addr, desc in sorted(self.__slaveDescs.items(),
						 key=lambda x: x[0])
			if addr != FdlTelegram.ADDRESS_MCAST
		]

		self.__runNextSlaveIndex = 0

	def getSlaveList(self):
		"""Get a list of registered DpSlaveDescs, sorted by address.
		"""
		return self.__slaveDescsList

	def _send(self, slave, telegram, timeout):
		"""Asynchronously send a telegram to a slave.
		"""
		slave.pendingReq = telegram
		slave.shortAckReceived = False
		try:
			if FdlTelegram.checkType(telegram):
				transceiver = self.fdlTrans
			else:
				transceiver = self.dpTrans
			print("XXX| Master sends frame of type %s at time: %d\nXXX| %s" 
		 			% (telegram.__class__, time.time(), telegram))
			transceiver.send(fcb=slave.fcb,
					 telegram=telegram)
		except ProfibusError as e:
			slave.pendingReq = None
			self.__masterSlowDown()
			self._debugMsg(str(e))
			return False
		self.__slowDownFact = 1
		slave.pendingReqTimeout.start(timeout)
		return True

	def _releaseSlave(self, slave):
		self.phy.releaseBus()

	def _runSlave_init(self, slave):
		if slave.stateJustEntered():
			self._debugMsg("Trying to initialize slave %d..." % (
				slave.slaveDesc.slaveAddr))
			slave.flushRxQueue()
		else:
			for telegram in slave.getRxQueue():
				if telegram.fc is not None:
					slave.pendingReq = None
					stype = telegram.fc & FdlTelegram.FC_STYPE_MASK
					if telegram.fc & FdlTelegram.FC_REQ:
						self._debugMsg("Slave %d replied with "
								"request bit set." %\
								slave.slaveDesc.slaveAddr)
					elif stype != FdlTelegram.FC_SLAVE:
						self._debugMsg("Device %d is not a slave. "
								"Detected type: 0x%02X" % (
								slave.slaveDesc.slaveAddr,
								stype))
					else:
						slave.setState(slave.STATE_WDIAG)
						return None
				else:
					self._debugMsg("Slave %d replied with a "
						"weird telegram:\n%s" % str(telegram))

		if (not slave.pendingReq or
		    slave.pendingReqTimeout.exceed()):
			# Reset fault debounce counter.
			slave.faultDeb.reset()

			# Disable the FCB bit.
			slave.fcb.enableFCB(False)

			ok = self._send(slave,
					 telegram=FdlTelegram_FdlStat_Req(
						da=slave.slaveDesc.slaveAddr,
						sa=self.masterAddr),
					 timeout=0.01)
			if not ok:
				self._debugMsg("FdlStat_Req failed")
				return None
		return None

	def _runSlave_waitDiag(self, slave):
		if slave.stateJustEntered():
			self._debugMsg("Requesting Slave_Diag from slave %d..." %\
				slave.slaveDesc.slaveAddr)
			slave.flushRxQueue()
		else:
			for telegram in slave.getRxQueue():
				if DpTelegram_SlaveDiag_Con.checkType(telegram):
					slave.setState(slave.STATE_WPRM)
					return None
				else:
					self._debugMsg("Received spurious "
						"telegram:\n%s" % str(telegram))

		if (not slave.pendingReq or
		    slave.pendingReqTimeout.exceed()):
			# Enable the FCB bit.
			slave.fcb.enableFCB(True)

			# Send a SlaveDiag request
			ok = self._send(slave,
					 telegram=DpTelegram_SlaveDiag_Req(
						da=slave.slaveDesc.slaveAddr,
						sa=self.masterAddr),
					 timeout=10)
			if not ok:
				self._debugMsg("SlaveDiag_Req failed")
				return None
		return None

	def _runSlave_waitPrm(self, slave):
		if slave.stateJustEntered():
			self._debugMsg("Sending Set_Prm to slave %d..." %\
				slave.slaveDesc.slaveAddr)
			slave.flushRxQueue()
		else:
			if slave.shortAckReceived:
				slave.fcb.handleReply()
				slave.setState(slave.STATE_WCFG)
				return None

		if (not slave.pendingReq or
		    slave.pendingReqTimeout.exceed()):
			# Send a Set_Prm request
			slave.slaveDesc.setPrmTelegram.sa = self.masterAddr
			ok = self._send(slave,
					 telegram=slave.slaveDesc.setPrmTelegram,
					 timeout=10)
			if not ok:
				self._debugMsg("Set_Prm failed")
				return None
		return None

	def _runSlave_waitCfg(self, slave):
		if slave.stateJustEntered():
			self._debugMsg("Sending Chk_Cfg to slave %d..." %\
				slave.slaveDesc.slaveAddr)
			slave.flushRxQueue()
		else:
			if slave.shortAckReceived:
				slave.fcb.handleReply()
				slave.setState(slave.STATE_WDXRDY)

		if (not slave.pendingReq or
		    slave.pendingReqTimeout.exceed()):
			slave.slaveDesc.chkCfgTelegram.sa = self.masterAddr
			ok = self._send(slave,
					 telegram=slave.slaveDesc.chkCfgTelegram,
					 timeout=10)
			if not ok:
				self._debugMsg("Chk_Cfg failed")
				return None
		return None

	def _runSlave_waitDxRdy(self, slave):
		if slave.stateJustEntered():
			self._debugMsg("Requesting Slave_Diag (WDXRDY) from slave %d..." %\
				slave.slaveDesc.slaveAddr)
			slave.flushRxQueue()
		else:
			for telegram in slave.getRxQueue():
				if DpTelegram_SlaveDiag_Con.checkType(telegram):
					if telegram.notExist():
						self.__errorMsg("Slave %d is not reachable "
							"via this line." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.cfgFault():
						self.__errorMsg("Slave %d reports a faulty "
							"configuration (Chk_Cfg)." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.prmFault():
						self.__errorMsg("Slave %d reports a faulty "
							"parameterization (Set_Prm)." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.prmReq():
						self._debugMsg("Slave %d requests a new "
							"parameterization (Set_Prm)." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.isNotSupp():
						self.__errorMsg("Slave %d replied with "
							"\"function not supported\". "
							"The parameters should be checked "
							"(Set_Prm)." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.masterLock():
						self.__errorMsg("Slave %d is already controlled "
							"(locked to) another DP-master." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if not telegram.hasOnebit():
						self._debugMsg("Slave %d diagnostic "
							"always-one-bit is zero." %\
							slave.slaveDesc.slaveAddr)
						slave.faultDeb.fault()
					if telegram.hasExtDiag():
						pass#TODO turn on red DIAG-LED
						slave.faultDeb.fault()

					if telegram.isReadyDataEx():
						slave.setState(slave.STATE_DX)
						return None
					if telegram.needsNewPrmCfg():
						slave.setState(slave.STATE_INIT)
						return None
					break
				else:
					self._debugMsg("Received spurious "
						"telegram:\n%s" % str(telegram))
					slave.faultDeb.fault()
		if (not slave.pendingReq or
		    slave.pendingReqTimeout.exceed()):
			ok = self._send(slave,
					 telegram=DpTelegram_SlaveDiag_Req(
						da=slave.slaveDesc.slaveAddr,
						sa=self.masterAddr),
					 timeout=0.05)
			if not ok:
				self._debugMsg("SlaveDiag_Req failed")
				slave.faultDeb.fault()
				return None
		self.__checkFaultDeb(slave, False)
		return None

	def _runSlave_dataExchange(self, slave):
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
					slave.faultDeb.fault()
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
		if self.__checkFaultDeb(slave, True):
			return None
		return dataExInData

	def __checkFaultDeb(self, slave, inDataExchange):
		faultCount = slave.faultDeb.get()
		if faultCount >= 5:
			# communication lost
			self._debugMsg("Communication lost in Data_Exchange or Slave_Diag.")
			slave.setState(slave.STATE_INIT)
			return True
		elif (faultCount >= 3 and
		      inDataExchange and
		      (monotonic_time() >= slave.dxStartTime + 0.2 or slave.slaveDesc.outputSize == 0)):
			# Diagnose the slave
			self._debugMsg("Many errors in Data_Exchange. "
					"Requesting diagnostic information...")
			slave.setState(slave.STATE_WDXRDY, 0.2)
			return True
		return False

	_slaveStateHandlers = {
		DpSlaveState.STATE_INIT		: _runSlave_init,
		DpSlaveState.STATE_WDIAG	: _runSlave_waitDiag,
		DpSlaveState.STATE_WPRM		: _runSlave_waitPrm,
		DpSlaveState.STATE_WCFG		: _runSlave_waitCfg,
		DpSlaveState.STATE_WDXRDY	: _runSlave_waitDxRdy,
		DpSlaveState.STATE_DX		: _runSlave_dataExchange,
	}

	def _runSlave(self, slave):
		self._pollRx()
		if not self.__haveToken:
			return None

		if slave.stateHasTimeout():
			self._debugMsg("State machine timeout! "
				"Trying to re-initializing slave %d..." %\
				slave.slaveDesc.slaveAddr)
			slave.setState(slave.STATE_INIT) 
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

	def _pollRx(self):
		try:
			ok, telegram = self.dpTrans.poll()
		except ProfibusError as e:
			self._debugMsg("RX error: %s" % str(e))
			return
		if ok and telegram:
			print("XXX| Master received frame of type %s at time: %d\nXXX| %s" 
		 		% (telegram.__class__, time.time(), telegram))
			if FdlTelegram_token.checkType(telegram):
				pass#TODO handle token
			elif FdlTelegram_ack.checkType(telegram):
				for addr, slave in self._slaveStates.items():
					if addr != FdlTelegram.ADDRESS_MCAST:
						slave.shortAckReceived = True
			elif telegram.da == FdlTelegram.ADDRESS_MCAST:
				self.__handleMcastTelegram(telegram)
			elif telegram.da == self.masterAddr:
				if telegram.sa in self._slaveStates:
					slave = self._slaveStates[telegram.sa]
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

	def __handleMcastTelegram(self, telegram):
		self._debugMsg("Received multicast telegram:\n%s" % str(telegram))
		pass#TODO

	def run(self):
		"""Run the DP-Master state machine.
		"""
		if self.debug:
			self.__runCount += 1
			now = monotonic_time()
			if now >= self.__runTimer + 10.0:
				cps = self.__runCount / (now - self.__runTimer)
				self._debugMsg("State machine calls: "
						"%.1f /s = %.3f s/call" % (
						cps, 1.0 / cps))
				self.__runTimer = now
				self.__runCount = 0

		if self.__slowDown:
			# Master slowdown is active.
			# Do not run state machine until the end of the slowdown.
			if monotonic_time() < self.__slowDownUntil:
				return None
			self.__slowDown = False

		slaveDescsList = self.__slaveDescsList
		runNextSlaveIndex = self.__runNextSlaveIndex

		if not slaveDescsList:
			return None

		slaveDesc = slaveDescsList[runNextSlaveIndex]
		self.__runNextSlaveIndex = (runNextSlaveIndex + 1) % len(slaveDescsList)

		slave = self._slaveStates[slaveDesc.slaveAddr]
		fromSlaveData = self._runSlave(slave)
		if (fromSlaveData is not None and
		    len(fromSlaveData) != slaveDesc.outputSize):
			self.__errorMsg("Slave %d: The received data size (%d bytes) "
					"does not match the slave's configured output_size (%d bytes)." % (
					slaveDesc.slaveAddr,
					len(fromSlaveData),
					slaveDesc.outputSize))
			slave.faultDeb.fault()
			fromSlaveData = None
		slave.fromSlaveData = fromSlaveData

		return slaveDesc

	def _setToSlaveData(self, slaveDesc, data):
		"""Set the master-out-data that will be sent the
		next time we are able to send something to that slave.
		"""
		if (data is not None and
		    len(data) != slaveDesc.inputSize):
			raise DpError("Slave %d: The setMasterOutData() data size (%d bytes) "
				      "does not match the slave's configured input_size (%d bytes)." % (
				      slaveDesc.slaveAddr,
				      len(data),
				      slaveDesc.inputSize))
		slave = self._slaveStates[slaveDesc.slaveAddr]
		slave.toSlaveData = data

	def _getFromSlaveData(self, slaveDesc):
		"""Get the latest received master-in-data.
		Returns None, if there was no received data.
		"""
		slave = self._slaveStates[slaveDesc.slaveAddr]
		fromSlaveData = slave.fromSlaveData
		slave.fromSlaveData = None
		return fromSlaveData

	def _slaveIsConnecting(self, slaveDesc):
		slave = self._slaveStates[slaveDesc.slaveAddr]
		return (not slave.dxCycleRunning and
		        slave.getState() != DpSlaveState.STATE_INIT)

	def _slaveIsConnected(self, slaveDesc):
		slave = self._slaveStates[slaveDesc.slaveAddr]
		return slave.dxCycleRunning

	def initialize(self):
		"""Initialize the DPM."""

		# Initialize the RX filter
		self.fdlTrans.setRXFilter([self.masterAddr,
					   FdlTelegram.ADDRESS_MCAST])
		# Free memory
		gc.collect()

	def __syncFreezeHelper(self, groupMask, controlCommand):
		slave = self._slaveStates[FdlTelegram.ADDRESS_MCAST]
		globCtl = DpTelegram_GlobalControl(da = FdlTelegram.ADDRESS_MCAST,
						   sa = self.masterAddr)
		globCtl.controlCommand |= controlCommand
		globCtl.groupSelect = groupMask & 0xFF
		self.dpTrans.send(fcb = slave.fcb,
				  telegram = globCtl)

	def syncMode(self, groupMask):
		"""Set SYNC-mode on the specified groupMask.
		If groupMask is 0, all slaves are addressed."""

		self.__syncFreezeHelper(groupMask, DpTelegram_GlobalControl.CCMD_SYNC)

	def syncModeCancel(self, groupMask):
		"""Cancel SYNC-mode on the specified groupMask.
		If groupMask is 0, all slaves are addressed."""

		self.__syncFreezeHelper(groupMask, DpTelegram_GlobalControl.CCMD_UNSYNC)

	def freezeMode(self, groupMask):
		"""Set FREEZE-mode on the specified groupMask.
		If groupMask is 0, all slaves are addressed."""

		self.__syncFreezeHelper(groupMask, DpTelegram_GlobalControl.CCMD_FREEZE)

	def freezeModeCancel(self, groupMask):
		"""Cancel FREEZE-mode on the specified groupMask.
		If groupMask is 0, all slaves are addressed."""

		self.__syncFreezeHelper(groupMask, DpTelegram_GlobalControl.CCMD_UNFREEZE)

class DPM1(DpMaster):
	def __init__(self, phy, masterAddr, debug=False):
		DpMaster.__init__(self, dpmClass=1, phy=phy,
			masterAddr=masterAddr,
			debug=debug)

class DPM2(DpMaster):
	def __init__(self, phy, masterAddr, debug=False):
		DpMaster.__init__(self, dpmClass=2, phy=phy,
			masterAddr=masterAddr,
			debug=debug)
