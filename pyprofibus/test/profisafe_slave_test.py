import sys
sys.path.insert(0, "/home/alessio/pyprofisafe")

import time

import pyprofibus
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.pyprofisafe.ProfiSafeError import ProfiSafeError
from pyprofibus.pyprofisafe.dp_profisafe.ControlByteDevice import ControlByteDevice
from pyprofibus.pyprofisafe.dp_profisafe.ProfiSafeTelegram_Con import ProfiSafeTelegram_Con
from pyprofibus.pyprofisafe.slave_profisafe.F_Device import F_Device
from pyprofibus.pyprofisafe.slave_profisafe.SafetyData_ExchState import SafetyData_ExchState
from pyprofibus.pyprofisafe.slave_profisafe.SafetyResetState import SafetyResetState
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.util import ProfibusError

from unittest import TestCase
import unittest

class TestSlaveProfisafe(TestCase):

    phy: CpPhySerial
    slave: F_Device

    @classmethod
    def setUpClass(cls):
        try:
            #init
            phy = CpPhySerial("/dev/ttyS0", True)
            cls.slave = F_Device(phy)
            cls.slave.setState(SafetyResetState())
            #slave.setState(Wait_PrmState(slave))
            #parameterization
            cls.slave.setAddress(0)
            cls.slave.setParameters(True, 50000, 100, False, False, 0, 111, "victim")
            cls.slave.setState(SafetyData_ExchState())

            

        except (ProfibusError, ProfiSafeError) as e:
            print("Terminating slave: %s" % str(e))
            return 1
        
        return 0

    #@unittest.skip("Skipping cyclic communication test")
    def testCyclicCommunicationSlave(self):
        out_du = bytearray()
        
        #run
        for i in range(4):
            #try:
            #    r = self.slave.receive(15)
            #except Exception as e:
            #    print(e)
            r = self.slave.receive(150)
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
            payload = DpTelegram_DataExchange_Con(
                 self.slave.getMasterAddress(),
                 self.slave.address,
                 FdlTelegram.FC_OK,
                 out_du
            )
            control_byte = ControlByteDevice(ControlByteDevice.TOGGLE_D)
            crc = b'\xab' * 24
            send_telegram = ProfiSafeTelegram_Con(payload, control_byte, crc)
            self.slave.send(send_telegram)
    
    @classmethod
    def tearDownClass(cls):
        import subprocess
        subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)
        #phy.close()
        

if __name__ == '__main__':
    unittest.main()