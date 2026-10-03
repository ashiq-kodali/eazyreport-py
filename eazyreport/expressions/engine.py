"""Handlebars-compatible pure Python expression tokenizer and evaluator.

Supports 35+ helpers, nested sub-expressions `(gt item.qty 10)`, dot-notation path traversal,
math, string operations, formatting, aggregates, and conditions without any JavaScript engine.
"""
import math
import re
from typing import Any, Callable, Dict, List, Optional, Union

from .format import escape_html, format_currency, format_date_pattern, format_number, to_date
from .number_to_words import number_to_words


def get_path(obj: Any, path: str) -> Any:
    """Traverse an object hierarchy using dot notation (e.g. 'company.address.city' or 'items.0.qty')."""
    if not path or obj is None:
        return None
    parts = path.split('.')
    curr = obj
    for part in parts:
        if curr is None:
            return None
        if isinstance(curr, dict):
            curr = curr.get(part)
        elif isinstance(curr, (list, tuple)):
            try:
                idx = int(part)
                if 0 <= idx < len(curr):
                    curr = curr[idx]
                else:
                    return None
            except ValueError:
                return None
        elif hasattr(curr, part):
            curr = getattr(curr, part)
        else:
            return None
    return curr


def _num(v: Any) -> Union[int, float]:
    """Coerce value to number, defaulting to 0."""
    if v is None or v == '':
        return 0
    if isinstance(v, (int, float)):
        return v
    try:
        f = float(str(v).replace(',', ''))
        return int(f) if f.is_integer() else f
    except (ValueError, TypeError):
        return 0


def _is_truthy(v: Any) -> bool:
    """Determine truthiness matching template engine conventions."""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        return bool(s and s not in ('false', '0', 'no', 'null', 'undefined'))
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) > 0
    return True


# Helper functions registry
EXPRESSION_HELPERS: Dict[str, Callable] = {}


def _register_helper(name: str):
    def decorator(fn: Callable):
        EXPRESSION_HELPERS[name] = fn
        return fn
    return decorator


@_register_helper('formatCurrency')
def _h_format_currency(v: Any, cur: str = 'USD', dec: Union[int, float] = 2) -> str:
    return format_currency(v, str(cur) if cur else 'USD', int(dec) if dec is not None else 2)


@_register_helper('formatNumber')
def _h_format_number(v: Any, dec: Union[int, float] = 2, thousands: bool = True) -> str:
    return format_number(v, int(dec) if dec is not None else 2, bool(thousands))


@_register_helper('formatDate')
def _h_format_date(v: Any, pattern: str = 'dd/MM/yyyy') -> str:
    d = to_date(v)
    if d is None:
        return str(v) if v is not None else ''
    return format_date_pattern(d, pattern or 'dd/MM/yyyy')


@_register_helper('formatPercent')
def _h_format_percent(v: Any, dec: Union[int, float] = 0) -> str:
    n = _num(v) * 100
    return f"{format_number(n, int(dec) if dec is not None else 0)}%"


@_register_helper('eq')
def _h_eq(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    try:
        na = float(str(a))
        nb = float(str(b))
        return na == nb
    except (ValueError, TypeError):
        pass
    return str(a if a is not None else '') == str(b if b is not None else '')


@_register_helper('ne')
def _h_ne(a: Any, b: Any) -> bool:
    return not _h_eq(a, b)


@_register_helper('gt')
def _h_gt(a: Any, b: Any) -> bool:
    return _num(a) > _num(b)


@_register_helper('gte')
def _h_gte(a: Any, b: Any) -> bool:
    return _num(a) >= _num(b)


@_register_helper('lt')
def _h_lt(a: Any, b: Any) -> bool:
    return _num(a) < _num(b)


@_register_helper('lte')
def _h_lte(a: Any, b: Any) -> bool:
    return _num(a) <= _num(b)


@_register_helper('and')
def _h_and(*args: Any) -> bool:
    flat_args = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            flat_args.extend(arg)
        else:
            flat_args.append(arg)
    return all(_is_truthy(a) for a in flat_args)


@_register_helper('or')
def _h_or(*args: Any) -> bool:
    flat_args = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            flat_args.extend(arg)
        else:
            flat_args.append(arg)
    return any(_is_truthy(a) for a in flat_args)


@_register_helper('not')
def _h_not(a: Any) -> bool:
    return not _is_truthy(a)


@_register_helper('iif')
def _h_iif(c: Any, a: Any, b: Any = '') -> Any:
    return a if _is_truthy(c) else (b if b is not None else '')


@_register_helper('isEmpty')
def _h_is_empty(v: Any) -> bool:
    if v is None or v == '':
        return True
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) == 0
    return False


@_register_helper('default')
def _h_default(v: Any, d: Any) -> Any:
    if v is None or v == '' or (isinstance(v, (list, tuple, dict, set)) and len(v) == 0):
        return d
    return v


@_register_helper('math')
def _h_math(a: Any, op: str, b: Any) -> Union[int, float]:
    l = _num(a)
    r = _num(b)
    if op == '+':
        res = l + r
    elif op == '-':
        res = l - r
    elif op == '*':
        res = l * r
    elif op == '/':
        res = (l / r) if r != 0 else 0
    elif op == '%':
        res = (l % r) if r != 0 else 0
    else:
        res = 0
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('add')
def _h_add(a: Any, b: Any) -> Union[int, float]:
    res = _num(a) + _num(b)
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('sub')
def _h_sub(a: Any, b: Any) -> Union[int, float]:
    res = _num(a) - _num(b)
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('mul')
def _h_mul(a: Any, b: Any) -> Union[int, float]:
    res = _num(a) * _num(b)
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('div')
def _h_div(a: Any, b: Any) -> Union[int, float]:
    r = _num(b)
    if r == 0:
        return 0
    res = _num(a) / r
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('round')
def _h_round(a: Any, d: Union[int, float] = 0) -> Union[int, float]:
    places = int(d) if d is not None else 0
    res = round(_num(a), places)
    return int(res) if places == 0 else res


@_register_helper('abs')
def _h_abs(a: Any) -> Union[int, float]:
    return abs(_num(a))


@_register_helper('sum')
def _h_sum(arr: Any, field: Optional[str] = None) -> Union[int, float]:
    if not isinstance(arr, (list, tuple)):
        return 0
    total = 0.0
    for it in arr:
        if field and isinstance(field, str) and field:
            clean_field = field[5:] if field.startswith('item.') else field
            total += float(_num(get_path(it, clean_field)))
        else:
            total += float(_num(it))
    return int(total) if total.is_integer() else total


@_register_helper('count')
def _h_count(arr: Any) -> int:
    return len(arr) if isinstance(arr, (list, tuple, dict, set)) else 0


@_register_helper('avg')
def _h_avg(arr: Any, field: Optional[str] = None) -> Union[int, float]:
    if not isinstance(arr, (list, tuple)) or not arr:
        return 0
    total = _h_sum(arr, field)
    res = total / len(arr)
    return int(res) if isinstance(res, float) and res.is_integer() else res


@_register_helper('join')
def _h_join(arr: Any, sep: str = ', ') -> str:
    if isinstance(arr, (list, tuple)):
        return sep.join(str(x) for x in arr)
    return ''


@_register_helper('uppercase')
def _h_uppercase(s: Any) -> str:
    return str(s if s is not None else '').upper()


@_register_helper('lowercase')
def _h_lowercase(s: Any) -> str:
    return str(s if s is not None else '').lower()


@_register_helper('titlecase')
def _h_titlecase(s: Any) -> str:
    words = re.split(r'\s+', str(s if s is not None else ''))
    return ' '.join(w.capitalize() for w in words if w)


@_register_helper('trim')
def _h_trim(s: Any) -> str:
    return str(s if s is not None else '').strip()


@_register_helper('substr')
def _h_substr(s: Any, start: Union[int, float], length: Optional[Union[int, float]] = None) -> str:
    txt = str(s if s is not None else '')
    st = max(0, min(len(txt), int(_num(start))))
    if length is not None:
        l = max(0, min(len(txt) - st, int(_num(length))))
        return txt[st:st + l]
    return txt[st:]


@_register_helper('left')
def _h_left(s: Any, n: Union[int, float]) -> str:
    txt = str(s if s is not None else '')
    count = max(0, min(len(txt), int(_num(n))))
    return txt[:count]


@_register_helper('right')
def _h_right(s: Any, n: Union[int, float]) -> str:
    txt = str(s if s is not None else '')
    count = max(0, min(len(txt), int(_num(n))))
    return txt[len(txt) - count:]


@_register_helper('padLeft')
def _h_pad_left(s: Any, n: Union[int, float], ch: str = '0') -> str:
    txt = str(s if s is not None else '')
    pad_char = ch[0] if ch else '0'
    return txt.rjust(int(_num(n)), pad_char)


@_register_helper('padRight')
def _h_pad_right(s: Any, n: Union[int, float], ch: str = ' ') -> str:
    txt = str(s if s is not None else '')
    pad_char = ch[0] if ch else ' '
    return txt.ljust(int(_num(n)), pad_char)


@_register_helper('replace')
def _h_replace(s: Any, a: Any, b: Any) -> str:
    return str(s if s is not None else '').replace(str(a if a is not None else ''), str(b if b is not None else ''))


@_register_helper('concat')
def _h_concat(*args: Any) -> str:
    flat_args = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            flat_args.extend(arg)
        else:
            flat_args.append(arg)
    return ''.join(str(e if e is not None else '') for e in flat_args)


@_register_helper('length')
def _h_length(v: Any) -> int:
    if isinstance(v, (str, list, tuple, dict, set)):
        return len(v)
    return 0


@_register_helper('numberToWords')
def _h_number_to_words(v: Any) -> str:
    return number_to_words(_num(v))


class _Token:
    def __init__(self, text: str, is_sub_expr: bool = False):
        self.text = text
        self.is_sub_expr = is_sub_expr

    def __repr__(self) -> str:
        return f"_Token({self.text!r}, sub={self.is_sub_expr})"


def _tokenize(input_str: str) -> List[_Token]:
    """Tokenize an expression into arguments, strings, and subexpressions."""
    tokens: List[_Token] = []
    i = 0
    n = len(input_str)

    while i < n:
        while i < n and input_str[i].isspace():
            i += 1
        if i >= n:
            break

        ch = input_str[i]

        # Quoted string literal
        if ch in ('"', "'"):
            quote = ch
            i += 1
            sb = []
            while i < n and input_str[i] != quote:
                if input_str[i] == '\\' and i + 1 < n:
                    i += 1
                    sb.append(input_str[i])
                else:
                    sb.append(input_str[i])
                i += 1
            if i < n:
                i += 1  # Skip closing quote
            tokens.append(_Token(f'"{("".join(sb))}"'))
            continue

        # Sub-expression in parenthesis (e.g. `(gt item.qty 10)`)
        if ch == '(':
            i += 1
            depth = 1
            sb = []
            while i < n and depth > 0:
                if input_str[i] == '(':
                    depth += 1
                elif input_str[i] == ')':
                    depth -= 1
                if depth > 0:
                    sb.append(input_str[i])
                i += 1
            tokens.append(_Token(''.join(sb).strip(), is_sub_expr=True))
            continue

        # Word, identifier, or literal
        sb = []
        while i < n and not input_str[i].isspace() and input_str[i] not in (')', '"', "'"):
            sb.append(input_str[i])
            i += 1
        tokens.append(_Token(''.join(sb)))

    return tokens


def _eval_token(token: _Token, ctx: Any) -> Any:
    """Evaluate a single token against context."""
    if token.is_sub_expr:
        return _eval_expression_string(token.text, ctx)

    raw = token.text
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    if raw == 'true':
        return True
    if raw == 'false':
        return False
    if raw == 'null':
        return None

    try:
        if '.' in raw or 'e' in raw.lower():
            return float(raw)
        return int(raw)
    except ValueError:
        pass

    # Resolve from context
    return get_path(ctx, raw)


def _eval_expression_string(expr: str, ctx: Any) -> Any:
    """Evaluate a space-separated expression with potential helper function."""
    tokens = _tokenize(expr.strip())
    if not tokens:
        return ''

    first_token = tokens[0]
    helper_name = first_token.text

    if not first_token.is_sub_expr and helper_name in EXPRESSION_HELPERS:
        helper = EXPRESSION_HELPERS[helper_name]
        arg_tokens = tokens[1:]
        evaluated_args = [_eval_token(t, ctx) for t in arg_tokens]
        try:
            return helper(*evaluated_args)
        except Exception:
            return ''

    if len(tokens) == 1:
        return _eval_token(first_token, ctx)

    return ' '.join(str(_eval_token(t, ctx) or '') for t in tokens)


def eval_template(tpl: str, ctx: Any) -> str:
    """Interpolate all `{{ ... }}` expressions within a template string and escape HTML."""
    if not tpl or '{{' not in tpl:
        return tpl or ''

    def _replace(match: re.Match) -> str:
        expr = match.group(1).strip()
        res = _eval_expression_string(expr, ctx)
        return escape_html(str(res)) if res is not None else ''

    return re.sub(r'\{\{([\s\S]*?)\}\}', _replace, tpl)


def eval_text(tpl: str, ctx: Any) -> str:
    """Interpolate expressions returning raw unescaped text."""
    h = eval_template(tpl, ctx)
    return (
        h.replace('&lt;', '<')
        .replace('&gt;', '>')
        .replace('&quot;', '"')
        .replace('&#x27;', "'")
        .replace('&#39;', "'")
        .replace('&#x3D;', '=')
        .replace('&#61;', '=')
        .replace('&#x60;', '`')
        .replace('&amp;', '&')
    )


def eval_condition(expr: str, ctx: Any) -> bool:
    """Evaluate a condition expression string to a boolean."""
    e = (expr or '').strip()
    if not e:
        return True
    if e == 'true':
        return True
    if e == 'false':
        return False
    if '{{' in e:
        out = eval_text(e, ctx).strip()
        return _is_truthy(out)

    parts = e.split(None, 1)
    if parts and parts[0] in EXPRESSION_HELPERS:
        res = _eval_expression_string(e, ctx)
        return _is_truthy(res)

    out = get_path(ctx, e)
    return _is_truthy(out)


def eval_value(expr: str, ctx: Any) -> Any:
    """Evaluate a single value expression or path."""
    e = (expr or '').strip()
    single_match = re.match(r'^\{\{\s*([\w.@$[\]]+)\s*\}\}$', e)
    if single_match:
        return get_path(ctx, single_match.group(1))
    if '{{' in e:
        return eval_text(e, ctx)
    return get_path(ctx, e)
