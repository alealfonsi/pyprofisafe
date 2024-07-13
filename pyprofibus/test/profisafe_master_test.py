import sys
import time

import pyprofibus
from pyprofibus.dp.dp import DpTelegram_SetPrm_Req
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.pyprofisafe.master_profisafe.F_Host import F_Host
sys.path.insert(0, "/home/alessio/pyprofisafe")

from unittest import TestCase
import unittest

class TestMasterProfisafe(TestCase):

    master: F_Host
    outData: bytearray

    @classmethod
    def setUpClass(cls) -> None:
        confdir="/home/alessio/pyprofisafe/pyprofibus/app_master"
        master = None
        try:
            # Parse the config file.
            config = pyprofibus.PbConf.fromFile(confdir + "/app_master.conf")

            # Create a DP master.
            master = config.makeProfiSafeDPM(CpPhySerial("/dev/ttyS0", True))

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
                prms = slaveConf.gsd.getUserPrmData(dp1PrmMask=dp1PrmMask, dp1PrmSet=dp1PrmSet)
                slaveDesc.setUserPrmData(prms)
                slaveDesc.setPrmTelegram.stationStatus = DpTelegram_SetPrm_Req.STA_LOCK

                # Register the slave at the DPM
                master.addSlave(slaveDesc, 600)

                # Set initial output data.
                cls.outData[slaveDesc.name] = bytearray((0x00, 0x00))
                

            cls.master = master
            # Initialize the DPM
            cls.master.initialize()  

        except pyprofibus.ProfibusError as e:
            print("Terminating: %s" % str(e))
            return 1
        return 0
    
    #@unittest.skip("Skipping cyclic communication test")
    def testCyclicCommunicationMaster(self):
        
        while True:
                # Write the output data.
                for slaveDesc in self.master.getSlaveList():
                    slaveDesc.setMasterOutData(self.outData[slaveDesc.name])

                # Run slave state machines.
                handledSlaveDesc = self.master.run()
                time.sleep(0.2)

                # Get the in-data (receive)
                if handledSlaveDesc:
                    inData = handledSlaveDesc.getMasterInData()
                    if inData is not None:
                        if inData[0] == 7 and inData[1] == 7:
                             break
                        self.outData[handledSlaveDesc.name][0] = inData[0] + 1
                        self.outData[handledSlaveDesc.name][1] = inData[1] + 1

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.master:
            cls.master.destroy()
            import subprocess
            subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)

if __name__ == '__main__':
     unittest.main()