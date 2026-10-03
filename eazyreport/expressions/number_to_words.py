"""Number to words converter for cheque / currency amounts."""
from typing import Union

ONES = [
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen'
]

TENS = [
    '', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'
]

SCALES = ['', 'Thousand', 'Million', 'Billion', 'Trillion']


def number_to_words(n: Union[int, float, str]) -> str:
    """Convert a numeric value to English words with optional cents (e.g. 125.50 -> One Hundred Twenty-Five and 50/100)."""
    try:
        val = float(n)
    except (ValueError, TypeError):
        return ''

    import math
    if math.isnan(val) or math.isinf(val):
        return ''

    abs_val = abs(val)
    whole = int(abs_val)
    cents = int(round((abs_val - whole) * 100))

    def chunk(x: int) -> str:
        parts = []
        if x >= 100:
            parts.append(f"{ONES[x // 100]} Hundred")
            x %= 100
        if x >= 20:
            t = TENS[x // 10]
            o = f"-{ONES[x % 10]}" if (x % 10 != 0) else ''
            parts.append(f"{t}{o}")
        elif x > 0:
            parts.append(ONES[x])
        return ' '.join(parts)

    rest = whole
    i = 0
    words = []
    if rest == 0:
        words.append('Zero')

    while rest > 0:
        c = rest % 1000
        if c != 0:
            s = f" {SCALES[i]}" if (i < len(SCALES) and SCALES[i]) else ''
            words.insert(0, f"{chunk(c)}{s}")
        rest //= 1000
        i += 1

    prefix = 'Minus ' if val < 0 else ''
    cents_text = f" and {cents:02d}/100" if cents > 0 else ''
    return f"{prefix}{' '.join(words)}{cents_text}"
