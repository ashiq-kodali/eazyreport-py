"""Formatting utilities for numbers, currencies, dates, and HTML escaping."""
import html
import re
from datetime import datetime, timezone
from typing import Any, Optional, Union

MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

DAYS = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]


def escape_html(s: Any) -> str:
    """Escape special HTML characters."""
    if s is None:
        return ''
    return html.escape(str(s), quote=True)


def to_date(value: Any) -> Optional[datetime]:
    """Parse various representations of date/time into a Python datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # Check if milliseconds or seconds
        if value > 1e11:
            return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        val_str = value.strip()
        if not val_str:
            return None
        # Try standard ISO formats
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ):
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(val_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            pass
    return None


def format_date_pattern(d: datetime, pattern: str = 'dd/MM/yyyy') -> str:
    """Format a datetime according to standard format tokens like dd/MM/yyyy, yyyy-MM-dd, HH:mm:ss, etc."""
    h12 = 12 if (d.hour % 12 == 0) else (d.hour % 12)
    tokens = {
        'yyyy': f"{d.year:04d}",
        'yy': f"{d.year % 100:02d}",
        'MMMM': MONTHS[d.month - 1],
        'MMM': MONTHS[d.month - 1][:3],
        'MM': f"{d.month:02d}",
        'M': str(d.month),
        'dddd': DAYS[d.weekday()],
        'ddd': DAYS[d.weekday()][:3],
        'dd': f"{d.day:02d}",
        'd': str(d.day),
        'HH': f"{d.hour:02d}",
        'H': str(d.hour),
        'hh': f"{h12:02d}",
        'h': str(h12),
        'mm': f"{d.minute:02d}",
        'ss': f"{d.second:02d}",
        'tt': 'AM' if d.hour < 12 else 'PM',
    }

    regex = re.compile(r'yyyy|yy|MMMM|MMM|MM|M|dddd|ddd|dd|d|HH|H|hh|h|mm|ss|tt')
    return regex.sub(lambda m: tokens.get(m.group(0), m.group(0)), pattern)


def format_number(value: Any, decimals: int = 2, thousands: bool = True) -> str:
    """Format a number with optional decimal places and thousands separator."""
    if value is None or value == '':
        return ''
    try:
        n = float(value)
    except (ValueError, TypeError):
        return ''

    if thousands:
        fmt = f",.{decimals}f"
    else:
        fmt = f".{decimals}f"
    return format(n, fmt)


CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'INR': '₹',
    'JPY': '¥',
    'CAD': 'CA$',
    'AUD': 'AU$',
    'CHF': 'CHF',
    'CNY': '¥',
    'AED': 'AED',
    'SAR': 'SAR',
}


def format_currency(value: Any, currency: str = 'USD', decimals: int = 2) -> str:
    """Format a numeric value as currency (e.g. $1,234.56)."""
    if value is None or value == '':
        return ''
    num_str = format_number(value, decimals=decimals, thousands=True)
    if not num_str:
        return ''

    cur_upper = currency.upper().strip()
    sym = CURRENCY_SYMBOLS.get(cur_upper, f"{cur_upper} ")
    return f"{sym}{num_str}"


def resolve_format_kind(format_name: str, data_type: str) -> str:
    """Resolve formatting kind from format property and data type."""
    if format_name and format_name != 'auto':
        return format_name
    if data_type == 'currency':
        return 'currency'
    if data_type == 'date':
        return 'date'
    if data_type == 'boolean':
        return 'boolean'
    return 'text'


def format_value(value: Any, fmt_spec: Optional[dict] = None, data_type: str = 'text') -> str:
    """Apply formatting rules to a value."""
    if value is None:
        return ''
    spec = fmt_spec or {}
    kind = resolve_format_kind(spec.get('format', 'auto'), data_type)
    decimals = int(spec.get('decimals', 2))
    thousands = bool(spec.get('thousands', True))
    currency = str(spec.get('currency', 'USD'))
    date_pattern = str(spec.get('datePattern', 'dd/MM/yyyy'))

    if kind == 'number':
        return format_number(value, decimals, thousands)
    if kind == 'currency':
        return format_currency(value, currency, decimals)
    if kind == 'date':
        d = to_date(value)
        return format_date_pattern(d, date_pattern) if d else str(value)
    if kind == 'percent':
        try:
            return f"{format_number(float(value) * 100, decimals, thousands)}%"
        except (ValueError, TypeError):
            return str(value)
    if kind == 'boolean':
        b = bool(value) if not isinstance(value, str) else value.lower() in ('true', '1', 'yes')
        return 'Yes' if b else 'No'

    return str(value)
