

class TextFormatter:
    @staticmethod
    def format_money(value: float, currency: str = "VND"):
        def _format_int_text(_value, pos=1):
            if len(_value) == 0:
                return ""
            last_value = _format_int_text(_value[:-1], pos=pos + 1)
            if pos % 3 == 0 and len(last_value) > 0:
                return last_value + f".{_value[-1]}"
            else:
                return last_value + f"{_value[-1]}"

        sub_value = value - int(value)
        value = int(value)
        if sub_value > 1e-4:
            output = _format_int_text(str(value)) + "," + str(sub_value)[2:6]
        else:
            output = _format_int_text(str(value))

        return f"{output} {currency}"

