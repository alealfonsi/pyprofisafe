from abc import ABC, abstractmethod

from pyprofibus.dp.dp import DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram, FdlTransceiver
from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

	__slave: Slave = None

	def receive(self, dpTrans):
		try:
			ok, telegram = dpTrans.poll()#check arguments
		except SlaveException as e:
			print("RX error: %s" % str(e))
			return
		if ok and telegram:
			if ((telegram.sa == self.getSlave().getMasterAddress()) and 
			((telegram.da == self.getAddress()) or (telegram.da == FdlTelegram.ADDRESS_MCAST))):
				self.getSlave().resetWatchdog()
				return self.checkTelegram(telegram)
		else:
			if telegram:
				print("Received corrupt telegram:\n%s" % str(telegram))
		
	def send(self, telegram, dpTrans):
		try:
			self.checkTelegramToSend(telegram)
			dpTrans.send()#check arguments
		except SlaveException as e:
			print(str(e))
		
	@abstractmethod
	def checkTelegram(self):
		"""Receive telegram"""
	
	@abstractmethod
	def checkTelegramToSend(self, telegram):
		"""Check that the telegram the slave wants to send is of the proper type and 
		if the slave is in a state in which is possible to send it"""

	def getSlave(self):
		return self.__slave
    
	def setSlave(self, slave):
		self.__slave = Slave
    
	@abstractmethod
	def setParameters(self,
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
	
	def getAddress(self):
		return self.__slave.address