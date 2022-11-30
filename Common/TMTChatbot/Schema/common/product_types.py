

class BillStatus:
    INIT = "INIT"
    PROCESSING = "PROCESSING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    DONE = "DONE"


class PaymentStatus:
    INIT = "INIT"
    PENDING = "PENDING"
    DONE = "DONE"


class ProductStatus:
    NONE = "NONE"
    CARE = "CARE"
    CANCELED = "CANCELED"
    CONFIRMED = "CONFIRMED"
    DONE = "DONE"


class BankVerificationMethod:
    NONE = "NONE"
    IMAGE = "IMAGE"
    SIGNAL = "SIGNAL"
