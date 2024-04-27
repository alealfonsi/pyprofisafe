import sys

sys.path.insert(0, "/home/alealfo/pyprofisafe")


from pyprofibus.slave.Slave import Slave
from pyprofibus.physical.phy import CpPhy
from pyprofibus.slave.Wait_PrmState import Wait_PrmState


class Dumb():
    
    def main():
        
        slave_1 = Slave(CpPhy)
        slave_2 = Slave(CpPhy)
        slave_3 = Slave(CpPhy)
        
        slave_1.setState(Wait_PrmState(slave_1))
        slave_2.setState(Wait_PrmState(slave_2))
        slave_3.setState(Wait_PrmState(slave_3))
        
        
    
        slave_1.setParameters(100, 100, False, False, 0, 1, "first")
        slave_2.setParameters(300, 300, True, False, 0, 3, "second")
        
        print(slave_3.wd_limit)
        print(slave_2.wd_limit) #should break
        #print(slave_3.wd_limit)
        print(slave_1.master_add)
        print(slave_2.master_add)
        #print(slave_3.master_add)

if __name__ == "__main__":
	Dumb.main()
    
