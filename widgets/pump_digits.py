from textual.widgets import Digits

class PumpDigits(Digits):
    def __init__(self, value: float = 0, max_digits: int = 8, max_decimals: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.max_decimals = max_decimals
        self.set_value(value)

    def truncate(self, f: float, n: int) -> str:
        '''Truncates/pads a float f to n decimal places without rounding'''
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return '.'.join([i, (d+'0'*n)[:n]])

    def set_value(self, value: float):
        max_digits = self.max_digits
        if self.max_decimals > 0: max_digits += 1
        max_decimals = self.max_decimals

        while max_decimals >= 0:
            str = self.truncate(value, max_decimals)
            if len(str) <= max_digits:
                self.update(str)
                return
            max_decimals -= 1

        # unable to display integer value
        self.update("-" * self.max_digits)
        pass