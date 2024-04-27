from abc import ABC, abstractmethod

from pyprofibus.dp.dp import DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlFCB, FdlTelegram, FdlTransceiver
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

	__slave = None
 
	def __init__(self, slave):
		self.__slave = slave

	def receive(self, dpTrans, timeout):
		try:
			ok, telegram = dpTrans.poll(timeout)
		except SlaveException as e:
			print("RX error: %s" % str(e))
			return False
		if ok and telegram:
			if ((telegram.sa == self.getSlave().getMasterAddress()) and 
			((telegram.da == self.getAddress()) or (telegram.da == FdlTelegram.ADDRESS_MCAST))):
				if self.checkTelegram(telegram):
					self.getSlave().resetWatchdog()
					return True
		else:
			if telegram:
				print("Received corrupt telegram:\n%s" % str(telegram))
			return False
		
	def send(self, telegram, dpTrans):
		try:
			self.checkTelegramToSend(telegram)
			dpTrans.send(FdlFCB(False), telegram) 
			#fcb is passed as disabled
			#this feature is not really part of Profibus DP, but of the 
			#standard Profibus. It will be useful with profisafe because
			#its functioning is very similar to the virtual monitoring number
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
		self.__slave = slave
    
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