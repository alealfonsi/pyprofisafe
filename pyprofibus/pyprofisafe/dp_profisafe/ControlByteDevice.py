from pyprofibus.pyprofisafe.dp_profisafe.ControlByte import ControlByte


class ControlByteDevice(ControlByte):

    ACK_PRM = 0x01
    DEVICE_FAULT = 0x02
    CRC_ERROR = 0x04
    WD_TIMEOUT = 0x08
    FV_ACTIVATED = 0x10
    TOGGLE_D = 0x20
    RESERVED = 0x40

    

    