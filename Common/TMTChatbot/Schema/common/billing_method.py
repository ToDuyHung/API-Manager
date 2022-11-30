class BaseValueMethod:
    @classmethod
    def keys(cls):
        return [val for attr, val in cls.__dict__.items() if not attr.startswith("__")]


class ShipMethod(BaseValueMethod):
    SHIP = "ship"
    DIRECTLY = "directly"


class PaymentMethod(BaseValueMethod):
    COD = "COD"
    transfer = "bank_transfer"
    directly = "directly"
