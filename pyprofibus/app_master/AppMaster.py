import sys
sys.path.insert(0, "/home/alessio/pyprofisafe")

from pyprofibus.master.SimpleMaster import SimpleMaster
from pyprofibus.physical.phy_serial import CpPhySerial
import pyprofibus

class AppMaster():
    
    def main(confdir="/home/alessio/pyprofisafe/pyprofibus/app_master"):
        master = None
        try:
            # Parse the config file.
            config = pyprofibus.PbConf.fromFile(confdir + "/app_master.conf")

            # Create a DP master.
            master = config.makeSimpleDPM(CpPhySerial("/dev/ttyS0", True))

            # Create the slave descriptions.
            outData = {}
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
                master.addSlave(slaveDesc, 60)

                # Set initial output data.
                outData[slaveDesc.name] = bytearray((0x12, 0x34))

            # Initialize the DPM
            master.initialize()

            # Run the slave state machine.
            while True:
                # Write the output data.
                for slaveDesc in master.getSlaveList():
                    slaveDesc.setMasterOutData(outData[slaveDesc.name])

                # Run slave state machines.
                handledSlaveDesc = master.run()

                # Get the in-data (receive)
                if handledSlaveDesc:
                    inData = handledSlaveDesc.getMasterInData()
                    if inData is not None:
                        # In our example the output data shall be the inverted input.
                        outData[handledSlaveDesc.name][0] = inData[1]
                        outData[handledSlaveDesc.name][1] = inData[0]   

        except pyprofibus.ProfibusError as e:
            print("Terminating: %s" % str(e))
            return 1
        finally:
            if master:
                master.destroy()
                import subprocess
                subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)
        return 0


          

if __name__ == "__main__":
	AppMaster.main()