import sys
import time

import pyprofibus
from pyprofibus.master.SimpleMaster import SimpleMaster
from pyprofibus.physical.phy_serial import CpPhySerial
sys.path.insert(0, "/home/alessio/pyprofisafe")

from unittest import TestCase
import unittest

class TestMaster(TestCase):

    master: SimpleMaster
    outData: bytearray

    @classmethod
    def setUpClass(cls, self) -> None:
        confdir="/home/alessio/pyprofisafe/pyprofibus/app_master"
        master = None
        try:
            # Parse the config file.
            config = pyprofibus.PbConf.fromFile(confdir + "/app_master.conf")

            # Create a DP master.
            master = config.makeSimpleDPM(CpPhySerial("/dev/ttyS0", True))

            # Create the slave descriptions.
            self.outData = {}
            for slaveConf in config.slaveConfs:
                slaveDesc = slaveConf.makeDpSlaveDesc()

                # Set User_Prm_Data
                dp1PrmMask = bytearray((pyprofibus.dp.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
                                        pyprofibus.dp.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
                                        0x00))
                dp1PrmSet  = bytearray((pyprofibus.dp.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
                                        pyprofibus.dp.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
                                        0x00))
                slaveDesc.setUserPrmData(slaveConf.gsd.getUserPrmData(dp1PrmMask=dp1PrmMask,
                                                                      dp1PrmSet=dp1PrmSet))

                # Register the slave at the DPM
                master.addSlave(slaveDesc, 600)

                # Set initial output data.
                self.outData[slaveDesc.name] = bytearray((0x12, 0x34))

            self.master = master
            # Initialize the DPM
            self.master.initialize()  

        except pyprofibus.ProfibusError as e:
            print("Terminating: %s" % str(e))
            return 1
        return 0
    
    def testCyclicCommunicationMaster(self):
        for i in range(10):
                # Write the output data.
                for slaveDesc in self.master.getSlaveList():
                    slaveDesc.setMasterOutData(self.outData[slaveDesc.name])

                # Run slave state machines.
                handledSlaveDesc = self.master.run()

                # Get the in-data (receive)
                if handledSlaveDesc:
                    inData = handledSlaveDesc.getMasterInData()
                    if i % 2 == 1:
                         assert(inData is not None)
                    if inData is not None:
                        # In our example the output data shall be the inverted input.
                        self.outData[handledSlaveDesc.name][0] = inData[1]
                        self.outData[handledSlaveDesc.name][1] = inData[0]  

    def testEnterClearModeMaster(self):
         self.assertFalse(self.master.clear_mode)
         for i in range(10):
            self.master.run()
            time.sleep(0.1)
         self.assertTrue(self.master.clear_mode)

    
    @classmethod
    def tearDownClass(cls, self) -> None:
        if self.master:
                self.master.destroy()
                import subprocess
                subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)