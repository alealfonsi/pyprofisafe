import sys
sys.path.insert(0, "/home/alessio/lib/pyprofisafe")

from pyprofibus.fieldbus_data_link.fdl import FdlTelegram
from pyprofibus.physical.phy_dummy import CpPhyDummySlave
from unittest import TestCase
import unittest

#from pyprofibus.dp import dp
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.Slave import Slave


class ProfibusTest(TestCase):

    def test_DataExchangeTelegram(self): 
        #init
        #phy = CpPhySerial("/dev/ttyS0", True)
        phy = CpPhyDummySlave()
        slave = Slave(phy)
        slave.setState(ResetState())
        #slave.setState(Wait_PrmState(slave))
        #parameterization
        slave.setAddress(0)
        slave.setParameters(True, 600000, 100, False, False, 0, 111, "first")
        slave.setState(Data_ExchState())
        
        out_du = bytearray()
        out_du.append(0x13)
        out_du.append(0x35)
        
        send_telegram = DpTelegram_DataExchange_Con(
                     da=slave.getMasterAddress(),
                     sa=slave.address,
                     fc=FdlTelegram.FC_DL,
                     du=out_du
                )
        print("Built telegram: %s" % send_telegram)
        assert(DpTelegram_DataExchange_Con.checkType(send_telegram))


if __name__ == '__main__':
    unittest.main()
