from abc import ABC, abstractmethod

from pyprofibus.dp.dp import DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlFCB, FdlTelegram, FdlTransceiver
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

	def receive(self, slave, timeout):
		try:
			ok, telegram = slave.dpTrans.poll(timeout)
		except SlaveException as e:
			print("RX error: %s" % str(e))
			return False
		if ok and telegram:
			if ((telegram.sa == slave.getMasterAddress()) and 
			((telegram.da == self.getAddress(slave)) or (telegram.da == FdlTelegram.ADDRESS_MCAST))):
				if self.checkTelegram(slave, telegram):
					slave.resetWatchdog()
					return True
		else:
			if telegram:
				print("Received corrupt telegram:\n%s" % str(telegram))
			return False
		
	def send(self, slave, telegram, dpTrans):
		try:
			self.checkTelegramToSend(slave, telegram)
			dpTrans.send(FdlFCB(False), telegram) 
			#fcb is passed as disabled
			#this feature is not really part of Profibus DP, but of the 
			#standard Profibus. It will be useful with profisafe because
			#its functioning is very similar to the virtual monitoring number
		except SlaveException as e:
			print(str(e))
		
	@abstractmethod
	def checkTelegram(self, telegram):
		"""Receive telegram"""
	
	@abstractmethod
	def checkTelegramToSend(self, slave, telegram):
		"""Check that the telegram the slave wants to send is of the proper type and 
		if the slave is in a state in which is possible to send it"""
    
	@abstractmethod
	def setParameters(self,
				slave,
                watchdog_ms: int,
                slave_reaction_time, 
                freeze_mode_enable,
                locked, 
                group, 
                master_add,
                id): 
		"""
        Sets the 7 mandatory parameter for a slave
        """
    
	@abstractmethod
	def setAddress(self, address):
		"""
        Sets the address of the slave at start up
        """
	
	def getAddress(self, slave):
		return slave.address
	