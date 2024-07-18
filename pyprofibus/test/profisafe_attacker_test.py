import sys

sys.path.insert(0, "/home/alessio/pyprofisafe")

from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.attacker.exploit_profisafe import ExploitProfiSafe
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteDevice import ControlByteDevice
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Con import ProfiSafeTelegram_Con
from pyprofibus.pyprofisafe.slave_profisafe.SafetyData_ExchState import SafetyData_ExchState
from pyprofibus.pyprofisafe.slave_profisafe.F_Device import F_Device
from pyprofibus.pyprofisafe.slave_profisafe.SafetyResetState import SafetyResetState
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.SlaveException import SlaveException

from unittest import TestCase
import unittest

class TestAttacker(TestCase):

    phy: CpPhySerial
    slave: F_Device
    attacker: ExploitProfiSafe

    @classmethod
    def setUpClass(cls):
        try:
            #init
            phy = CpPhySerial("/dev/ttyS0", True)
            cls.slave = F_Device(phy)
            cls.slave.setState(SafetyResetState())
            #slave.setState(Wait_PrmState(slave))
            #parameterization
            cls.slave.setAddress(1)
            cls.slave.setParameters(False, 30000, 100, False, False, 0, 111, "attacker")
            cls.slave.setState(SafetyData_ExchState())
            cls.attacker = ExploitProfiSafe(cls.slave, 0, 0xA)

            

        except ProfiSafeError as e:
            print("Terminating slave: %s" % str(e))
            return 1
        
        return 0

    #@unittest.skip("Skipping test")
    def testAttack(self):

        ### normal data exchange with master
        out_du = bytearray()
        
        for i in range(2):
            r = self.slave.receive(15)
            if not r:
                raise SlaveException("Did't receive anything!")
            print("Slave " + self.slave.getId() + " received the telegram: %s" % self.slave.rx_telegram)
            #answer the master sending back the same data incremented by 1
            in_du = self.slave.rx_telegram.payload.getDU()
            if i == 0:
                out_du.append(in_du[0] + 1)
                out_du.append(in_du[1] + 1)
            else:
                out_du[0] = in_du[0] + 1
                out_du[1] = in_du[1] + 1
            payload = DpTelegram_DataExchange_Con(
                 self.slave.getMasterAddress(),
                 self.slave.address,
                 FdlTelegram.FC_OK,
                 out_du
            )
            control_byte = ControlByteDevice.TOGGLE_D
            crc = b'\xab' * 3
            send_telegram = ProfiSafeTelegram_Con(payload, control_byte, crc)
            self.slave.send(send_telegram)
        
        ### Run the exploit
        self.attacker.run()

    @classmethod
    def tearDownClass(cls):
        
        import subprocess
        subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)        

if __name__ == '__main__':
    unittest.main()