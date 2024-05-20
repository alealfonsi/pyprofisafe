import sys
sys.path.insert(0, "/home/alessio/pyprofisafe")


import time
import pyprofibus
from pyprofibus.dp.dp import DpTelegram_SetPrm_Req
from pyprofibus.master.SimpleMaster import SimpleMaster
from pyprofibus.physical.phy_serial import CpPhySerial

from unittest import TestCase
import unittest

class TestMaster(TestCase):

    master: SimpleMaster
    outData: bytearray

    @classmethod
    def setUpClass(cls) -> None:
        confdir="/home/alessio/pyprofisafe/pyprofibus/app_master"
        master = None
        try:
            # Parse the config file.
            config = pyprofibus.PbConf.fromFile(confdir + "/app_master.conf")

            # Create a DP master.
            master = config.makeSimpleDPM(CpPhySerial("/dev/ttyS0", True))

            # Create the slave descriptions.
            cls.outData = {}
            for slaveConf in config.slaveConfs:
                slaveDesc = slaveConf.makeDpSlaveDesc()

                # Set User_Prm_Data
                dp1PrmMask = bytearray((DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
                                        DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
                                        0x00))
                dp1PrmSet  = bytearray((DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
                                        DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
                                        0x00))
                slaveDesc.setUserPrmData(slaveConf.gsd.getUserPrmData(dp1PrmMask=dp1PrmMask,
                                                                      dp1PrmSet=dp1PrmSet))

                # Register the slave at the DPM
                master.addSlave(slaveDesc, 600)

                # Set initial output data.
                cls.outData[slaveDesc.name] = bytearray((0x12, 0x34))

            cls.master = master
            # Initialize the DPM
            cls.master.initialize()  

        except pyprofibus.ProfibusError as e:
            print("Terminating: %s" % str(e))
            return 1
        return 0
    
    def testCyclicCommunicationMaster(self):

        for i in range(10):
                ##### only for debug #####
                if i % 2 == 0:
                    """"""
                ##########################
                # Write the output data.
                for slaveDesc in self.master.getSlaveList():
                    slaveDesc.setMasterOutData(self.outData[slaveDesc.name])

                # Run slave state machines.
                handledSlaveDesc = self.master.run()
                time.sleep(0.2)

                # Get the in-data (receive)
                if handledSlaveDesc:
                    inData = handledSlaveDesc.getMasterInData()
                    #if i % 2 == 1:
                    #     assert(inData is not None)
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
    def tearDownClass(cls) -> None:
        if cls.master:
                cls.master.destroy()
                import subprocess
                subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)

if __name__ == '__main__':
     unittest.main()