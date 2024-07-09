from pyprofibus.util import ProfibusError


class ProfiSafeError(ProfibusError):
    
    def __init__(self, message):
        super().__init__(message)