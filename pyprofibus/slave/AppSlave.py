import sys
sys.path.insert(0, "/home/alessio/lib/pyprofisafe")
import pyprofibus

from pyprofibus.slave.Data_ExchState import Data_ExchState
from pyprofibus.dp.dp import DpTelegram_DataExchange_Con
from pyprofibus.physical.phy_serial import CpPhySerial
from pyprofibus.slave.ResetState import ResetState
from pyprofibus.slave.Slave import Slave
from pyprofibus.slave.SlaveException import SlaveException
from pyprofibus.slave.Wait_PrmState import Wait_PrmState


class AppSlave():
    def main():
        try:
            #init
            phy = CpPhySerial("/dev/ttyS0", True)
            slave = Slave(phy)
            slave.setState(ResetState())
            #slave.setState(Wait_PrmState(slave))
            #parameterization
            slave.setAddress(0)
            slave.setParameters(True, 600000, 100, False, False, 0, 111, "first")
            slave.setState(Data_ExchState())

            out_du = bytearray()

            #run
            while True:
                r = slave.receive(15)
                if not r:
                    raise SlaveException("Did't receive anything!")
                print("Slave " + slave.getId() + " received the telegram: %s" % slave.rx_telegram)

                #answer the master sending back the same data incremented by 1
                in_du = slave.rx_telegram.getDU()
                out_du.append(in_du[0] + 1)
                out_du.append(in_du[1] + 1)
                send_telegram = DpTelegram_DataExchange_Con(
                     slave.getMasterAddress(),
                     slave.address,
                     slave.rx_telegram.fc,
                     out_du
                )
                slave.send(send_telegram)

        except pyprofibus.ProfibusError as e:
            print("Terminating slave: %s" % str(e))
            return 1
        finally:
            if phy:
                import subprocess
                subprocess.run("stty -F /dev/ttyS0 sane", shell=True, capture_output=True, text=True)
                #phy.close()
        return 0

if __name__ == "__main__":
	AppSlave.main()