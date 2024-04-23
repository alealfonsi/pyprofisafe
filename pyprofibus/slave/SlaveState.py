from abc import ABC, abstractmethod

from pyprofibus.dp.dp import DpTransceiver
from pyprofibus.fieldbus_data_link.fdl import FdlTransceiver
from pyprofibus.slave.Slave import Slave, SlaveException
from pyprofibus.util import TimeLimit

class SlaveState(ABC):

	__slave: Slave = None

	def receive(self):
		dpTrans = self.getSlave().getDpTrans()
            
		try:
			ok, telegram = dpTrans.poll()
		except SlaveException as e:
			print("RX error: %s" % str(e))
			return
		if ok and telegram:
			if (telegram.sa == self.getSlave().getMasterAddress()) and (telegram.da == self.getAddress()):
				self.getSlave().resetWatchdog()
				self.__checkTelegram(telegram)
		else:
			if telegram:
				print("Received corrupt telegram:\n%s" % str(telegram))
		
	@abstractmethod
	def __checkTelegram(self):
		"""Receive telegram"""

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