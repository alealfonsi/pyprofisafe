from pyprofibus.pyprofisafe.dp_profisafe.ControlByte import ControlByte


class ControlByteHost(ControlByte):
    
    IPAR_EN = 0x01
    OPERATOR_ACK_REQUESTED = 0x02
    RESET_MNR = 0x04
    USE_WD_2 = 0x08
    ACTIVATE_FV = 0x10
    TOGGLE_H = 0x20
    OPERATOR_ACK = 0x40
    LOOPBACK = 0x80

    def isClear(self, old_toggle_h) -> bool:
        clear = True
        status = (
            self.IPAR_EN + 
            self.OPERATOR_ACK_REQUESTED +
            self.RESET_MNR +
            self.USE_WD_2 +
            self.ACTIVATE_FV
            ) & self.data
        if (status 
            or (old_toggle_h == (self.TOGGLE_H & self.data))
            or not(self.LOOPBACK & self.data)):
            clear = False
        return clear
            
        