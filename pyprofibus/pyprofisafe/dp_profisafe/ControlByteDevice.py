from pyprofibus.pyprofisafe.dp_profisafe.ControlByte import ControlByte


class ControlByteDevice(ControlByte):

    ACK_PRM = 0x01
    DEVICE_FAULT = 0x02
    CRC_ERROR = 0x04
    WD_TIMEOUT = 0x08
    FV_ACTIVATED = 0x10
    TOGGLE_D = 0x20
    RESERVED = 0x40

    def isClear(self, old_toggle_d) -> bool:
        clear = True
        status = (
            self.CRC_ERROR +
            self.WD_TIMEOUT +
            self.FV_ACTIVATED
        ) & self.data
        if (status 
            or (old_toggle_d == (self.TOGGLE_D & self.data))
            or self.RESERVED & self.data):
            clear = False
        return clear

    