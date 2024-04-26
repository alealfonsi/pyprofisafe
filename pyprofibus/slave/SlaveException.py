from pyprofibus.util import ProfibusError


class SlaveException(ProfibusError):
    def __init__(self, message):
        super().__init__(message)

class WatchdogExpiredException(SlaveException):
    def __init__(self, message):
        super().__init__(message)