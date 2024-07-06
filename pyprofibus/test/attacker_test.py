import sys

sys.path.insert(0, "/home/alessio/pyprofisafe")
import time

import pyprofibus
from pyprofibus.attacker.exploit_profibus import ExploitProfibus
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveException import SlaveException

from unittest import TestCase
import unittest

class TestAttacker(TestCase):

    phy: CpPhySerial
    slave: Slave
    attacker: ExploitProfibus

    @classmethod
    def setUpClass(cls):
        try:
            #init
            phy = CpPhySerial("/dev/ttyS0", True)
            cls.slave = Slave(phy)
            cls.slave.setState(ResetState())
            #slave.setState(Wait_PrmState(slave))
            #parameterization
            cls.slave.setAddress(1)
            cls.slave.setParameters(False, 30000, 100, False, False, 0, 111, "attacker")
            cls.slave.setState(Data_ExchState())
            cls.attacker = ExploitProfibus(cls.slave, 0, 0xA)

            

        except pyprofibus.ProfibusError as e:
            print("Terminating slave: %s" % str(e))
            return 1
        
        return 0

    #@unittest.skip("Skipping test")
    def testAttack(self):

        ### normal data exchange with master
        out_du = bytearray()
        
        for i in range(3):
            r = self.slave.receive(15)
            if not r:
                raise SlaveException("Did't receive anything!")
            print("Slave " + self.slave.getId() + " received the telegram: %s" % self.slave.rx_telegram)
            #answer the master sending back the same data incremented by 1
            in_du = self.slave.rx_telegram.getDU()
            if i == 0:
                out_du.append(in_du[0] + 1)
                out_du.append(in_du[1] + 1)
            else:
                out_du[0] = in_du[0] + 1
                out_du[1] = in_du[1] + 1
            send_telegram = DpTelegram_DataExchange_Con(
                 self.slave.getMasterAddress(),
                 self.slave.address,
                 FdlTelegram.FC_OK,
                 out_du
            )
            self.slave.send(send_telegram)
        
        ### Run the exploit
        self.attacker.run()

    @classmethod
    def tearDownClass(cls):
        
        import subprocess
        subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)        

if __name__ == '__main__':
    unittest.main()