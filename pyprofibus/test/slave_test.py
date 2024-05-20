import sys
sys.path.insert(0, "/home/alessio/pyprofisafe")

from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.slave.FailSafeProfibusState import FailSafeProfibusState

import pyprofibus
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveException import SlaveException, WatchdogExpiredException

from unittest import TestCase
import unittest

class TestSlave(TestCase):

    phy: CpPhySerial
    slave: Slave

    @classmethod
    def setUpClass(cls):
        try:
            #init
            phy = CpPhySerial("/dev/ttyS0", True)
            cls.slave = Slave(phy)
            cls.slave.setState(ResetState())
            #slave.setState(Wait_PrmState(slave))
            #parameterization
            cls.slave.setAddress(0)
            cls.slave.setParameters(200000, 100, False, False, 0, 111, "first")
            cls.slave.setState(Data_ExchState())

            

        except pyprofibus.ProfibusError as e:
            print("Terminating slave: %s" % str(e))
            return 1
        
        return 0

    def testCyclicCommunicationSlave(self):
        out_du = bytearray()
        
        #run
        for i in range(5):
            r = self.slave.receive(15)
            if not r:
                raise SlaveException("Did't receive anything!")
            print("Slave " + self.slave.getId() + " received the telegram: %s" % self.slave.rx_telegram)
            #answer the master sending back the same data incremented by 1
            in_du = self.slave.rx_telegram.getDU()
            out_du.append(in_du[0] + 1)
            out_du.append(in_du[1] + 1)
            send_telegram = DpTelegram_DataExchange_Con(
                 self.slave.getMasterAddress(),
                 self.slave.address,
                 FdlTelegram.FC_OK,
                 #self.slave.rx_telegram.fc,
                 out_du
            )
            self.slave.send(send_telegram)

    def testEnterClearModeSlave(self):
        try:
            while True:
                self.slave.receive(0.1)
        except WatchdogExpiredException:
            self.assertTrue(isinstance(self.slave.getState(), FailSafeProfibusState))
        
    @classmethod
    def tearDownClass(cls):
        
        import subprocess
        subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)
        #phy.close()
        

if __name__ == '__main__':
    unittest.main()