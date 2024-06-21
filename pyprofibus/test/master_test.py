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
    
    @unittest.skip("Skipping cyclic communication test")
    def testCyclicCommunicationMaster(self):
        c = 0

        while True:
                # Write the output data.
                for slaveDesc in self.master.getSlaveList():
                    slaveDesc.setMasterOutData(self.outData[slaveDesc.name])

                # Run slave state machines.
                handledSlaveDesc = self.master.run()
                c += 1
                time.sleep(0.2)

                # Get the in-data (receive)
                if handledSlaveDesc:
                    inData = handledSlaveDesc.getMasterInData()
                    if inData is not None:
                        if inData[0] == 0x09 and inData[1] == 0x09:
                             print(c)
                             break
                        self.outData[handledSlaveDesc.name][0] = inData[0] + 1
                        self.outData[handledSlaveDesc.name][1] = inData[1] + 1


    @unittest.skip("Skipping enter clear mode test")
    def testEnterClearModeMaster(self):
         self.assertFalse(self.master.clear_mode)
         desc = self.master.getSlaveList()
         desc[0].setMasterOutData(bytearray((0x66, 0x66)))
         for i in range(400):
            self.master.run()
            time.sleep(0.1)
         self.assertTrue(self.master.clear_mode)
    
    #@unittest.skip("Skipping test")
    def testReparameterizationAfterFailSafeModeMaster(self):

        #run normal data exchange
        while True:
            for slaveDesc in self.master.getSlaveList():
                slaveDesc.setMasterOutData(self.outData[slaveDesc.name])
            
            handledSlaveDesc = self.master.run()
            time.sleep(0.2)
            # Get the in-data (receive)
            if handledSlaveDesc:
                inData = handledSlaveDesc.getMasterInData()
                if inData is not None:
                    if inData[0] == 0x01 and inData[1] == 0x01:
                         break
                    self.outData[handledSlaveDesc.name][0] = inData[0] + 1
                    self.outData[handledSlaveDesc.name][1] = inData[1] + 1
        
        #go to Clear Mode and reparameterize the slave

        went_to_clear_mode = False
        while (went_to_clear_mode is False) or (self.master.clear_mode is True):
            handledSlaveDesc = self.master.run()

            if handledSlaveDesc:
                self.outData[handledSlaveDesc.name][0] = 0x99
                self.outData[handledSlaveDesc.name][1] = 0x99
            
            if (went_to_clear_mode is False) and (self.master.clear_mode is True):
                went_to_clear_mode = True
        
        #assert everything is ok
        self.assertFalse(self.master.clear_mode is False)
    
    @classmethod
    def tearDownClass(cls) -> None:
        if cls.master:
                cls.master.destroy()
                import subprocess
                subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)

if __name__ == '__main__':
     unittest.main()