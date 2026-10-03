"""Pure Python Barcode and QR code SVG generator."""
import re
from typing import Dict, List, Optional

from ..expressions.format import escape_html
from ..model.types import LayoutElement


def is_two_dimensional(symbology: str) -> bool:
    s = (symbology or '').lower()
    return s in ('qrcode', 'microqrcode', 'swissqrcode', 'datamatrix', 'pdf417', 'aztec')


# Code 128 B Character Table (patterns of bar/space widths)
CODE128_B_PATTERNS = {
    ' ': '212222', '!': '222122', '"': '222221', '#': '121223', '$': '121322',
    '%': '131222', '&': '122213', "'": '122312', '(': '132212', ')': '221213',
    '*': '221312', '+': '231212', ',': '112232', '-': '122132', '.': '122231',
    '/': '113222', '0': '123122', '1': '123221', '2': '223211', '3': '221132',
    '4': '221231', '5': '213212', '6': '223112', '7': '312131', '8': '311222',
    '9': '321122', ':': '321221', ';': '312212', '<': '322112', '=': '322211',
    '>': '212123', '?': '212321', '@': '232121', 'A': '111323', 'B': '131123',
    'C': '131321', 'D': '112313', 'E': '132113', 'F': '132311', 'G': '211313',
    'H': '231113', 'I': '231311', 'J': '112133', 'K': '112331', 'L': '132131',
    'M': '113123', 'N': '113321', 'O': '133121', 'P': '313121', 'Q': '211331',
    'R': '231131', 'S': '213113', 'T': '213311', 'U': '213131', 'V': '311123',
    'W': '311321', 'X': '331121', 'Y': '312113', 'Z': '312311', '[': '332111',
    '\\': '314111', ']': '221411', '^': '431111', '_': '111224', '`': '111422',
    'a': '121124', 'b': '121421', 'c': '141122', 'd': '141221', 'e': '112214',
    'f': '112412', 'g': '122114', 'h': '122411', 'i': '142112', 'j': '142211',
    'k': '241211', 'l': '221114', 'm': '413111', 'n': '241112', 'o': '134111',
    'p': '111242', 'q': '121142', 'r': '121241', 's': '114212', 't': '124112',
    'u': '124211', 'v': '411212', 'w': '421112', 'x': '421211', 'y': '212141',
    'z': '214121', '{': '412121', '|': '111143', '}': '111341', '~': '131141',
}

START_B = '211214'
STOP_PATTERN = '2331112'


def _encode_code128(text: str) -> str:
    """Encode ASCII string into Code 128 B pattern of widths."""
    widths = [START_B]
    check_sum = 104  # Start Code B index
    pos = 1

    for ch in text:
        if ch in CODE128_B_PATTERNS:
            pat = CODE128_B_PATTERNS[ch]
            char_val = ord(ch) - 32
            check_sum += char_val * pos
            widths.append(pat)
            pos += 1

    # Checksum character
    check_val = check_sum % 103
    check_ch = chr(check_val + 32) if (check_val + 32) in range(32, 127) else ' '
    widths.append(CODE128_B_PATTERNS.get(check_ch, '212222'))
    widths.append(STOP_PATTERN)
    return ''.join(widths)


def _qr_to_svg(val: str, bar_color: str, bg_color: str, w: float, h: float) -> str:
    """Generate QR code SVG."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(val)
        qr.make(fit=True)
        matrix = qr.get_matrix()
    except Exception:
        # Fallback 21x21 mock matrix
        matrix = [[(i + j) % 2 == 0 for j in range(21)] for i in range(21)]

    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0

    rects = []
    if bg_color and bg_color.lower() != 'transparent':
        rects.append(f'<rect width="{cols}" height="{rows}" fill="{bg_color}"/>')

    for r_idx, row in enumerate(matrix):
        for c_idx, cell in enumerate(row):
            if cell:
                rects.append(f'<rect x="{c_idx}" y="{r_idx}" width="1" height="1" fill="{bar_color}"/>')

    return (
        f'<svg viewBox="0 0 {cols} {rows}" preserveAspectRatio="xMidYMid meet" '
        f'style="display:block;width:100%;height:100%" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(rects)}</svg>'
    )


def _linear_to_svg(val: str, bar_color: str, bg_color: str, show_text: bool) -> str:
    """Generate 1D barcode SVG (Code 128)."""
    pattern = _encode_code128(val)

    # Calculate total module width
    total_modules = sum(int(digit) for digit in pattern)
    bar_height = 80 if show_text else 100
    svg_height = 100
    svg_width = total_modules + 20

    rects = []
    if bg_color and bg_color.lower() != 'transparent':
        rects.append(f'<rect width="{svg_width}" height="{svg_height}" fill="{bg_color}"/>')

    curr_x = 10.0
    is_bar = True
    for digit in pattern:
        mod_w = int(digit)
        if is_bar:
            rects.append(
                f'<rect x="{curr_x:.1f}" y="5" width="{mod_w}" height="{bar_height}" fill="{bar_color}"/>'
            )
        curr_x += mod_w
        is_bar = not is_bar

    if show_text:
        rects.append(
            f'<text x="{svg_width / 2:.1f}" y="95" text-anchor="middle" font-family="monospace" '
            f'font-size="12" fill="{bar_color}">{escape_html(val)}</text>'
        )

    return (
        f'<svg viewBox="0 0 {svg_width} {svg_height}" preserveAspectRatio="none" '
        f'style="display:block;width:100%;height:100%" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(rects)}</svg>'
    )


def barcode_svg(el: LayoutElement, value: str) -> str:
    """Generate an SVG barcode matching element settings."""
    val = value or el.barcodeValue or '12345678'
    bar_color = el.barColor or '#000000'
    bg_color = el.barcodeBackground or '#ffffff'

    if is_two_dimensional(el.symbology):
        return _qr_to_svg(val, bar_color, bg_color, el.w, el.h)
    return _linear_to_svg(val, bar_color, bg_color, el.showText)


def barcode_html(el: LayoutElement, value: str) -> str:
    """Return HTML container wrapping the barcode SVG."""
    svg = barcode_svg(el, value)
    return f'<div class="report-barcode" style="width:100%;height:100%;overflow:hidden;">{svg}</div>'
