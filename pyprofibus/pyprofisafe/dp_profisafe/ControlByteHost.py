from pyprofibus.pyprofisafe.dp_profisafe.ControlByte import ControlByte


class ControlByteHost(ControlByte):
    
    IPAR_EN = 0x01
    OPERATOR_ACK_REQUESTED = 0x02
    RESET_VMN = 0x04
    USE_WD_2 = 0x08
    ACTIVATE_FV = 0x10
    TOGGLE_H = 0x20
    OPERATOR_ACK = 0x40
    LOOPBACK = 0x80