from __future__ import division, absolute_import, print_function, unicode_literals
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.Slave import Slave
from pyprofibus_tstlib import *
initTest(__file__)

class Test_MasterSlaveProfibus():
    
    def test_DataExchangeTelegram():
        #init
        phy = CpPhySerial("/dev/ttyS0", True)
        slave = Slave(phy)
        slave.setState(ResetState())
        #slave.setState(Wait_PrmState(slave))
        #parameterization
        slave.setAddress(0)
        slave.setParameters(600000, 100, False, False, 0, 111, "first")
        slave.setState(Data_ExchState())
        
        out_du = bytearray()
        
        send_telegram = DpTelegram_DataExchange_Con(
                     slave.getMasterAddress(),
                     slave.address,
                     slave.rx_telegram.fc,
                     out_du
                )
        print("Built telegram: %s" % send_telegram)
        assert(DpTelegram_DataExchange_Con.checkType(send_telegram))