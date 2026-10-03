"""FastReport style conditional logic evaluation engine."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from ..expressions.engine import get_path
from ..model.types import LogicRule


def resolve_property_value(prop: str, ctx: Any) -> Any:
    """Resolve a property name against evaluation context."""
    if not prop or ctx is None:
        return None
    p = prop.strip()

    if isinstance(ctx, dict):
        if p.startswith('params.'):
            key = p[7:]
            params_dict = ctx.get('params')
            return params_dict.get(key) if isinstance(params_dict, dict) else None

        if p in ('Row', 'row'):
            return ctx.get('Row', ctx.get('rowNumber'))
        if p in ('Page', 'page'):
            return ctx.get('Page', 1)
        if p == 'TotalPages':
            return ctx.get('TotalPages', 1)
        if p == 'Now':
            return ctx.get('Now', datetime.now(timezone.utc).isoformat())

        row = ctx.get('row')
        if isinstance(row, dict) and p in row:
            return row[p]

    val = get_path(ctx, p)
    if val is not None:
        return val

    if isinstance(ctx, dict) and 'data' in ctx:
        return get_path(ctx['data'], p)

    return None


def check_condition(val: Any, op: str, cmp_val: Optional[str] = None) -> bool:
    """Check condition operator between val and cmp_val."""
    operator = (op or 'equals').lower()

    if operator == 'empty':
        if val is None or val == '':
            return True
        if isinstance(val, (list, tuple, dict, set)):
            return len(val) == 0
        return False

    if operator == 'not_empty':
        return not check_condition(val, 'empty')

    if operator == 'equals':
        if val is None:
            return cmp_val is None or cmp_val == ''
        try:
            n_val = float(str(val))
            n_cmp = float(str(cmp_val))
            return n_val == n_cmp
        except (ValueError, TypeError):
            pass
        return str(val).strip().lower() == str(cmp_val or '').strip().lower()

    if operator == 'not_equals':
        return not check_condition(val, 'equals', cmp_val)

    if operator in ('gt', 'gte', 'lt', 'lte'):
        try:
            n1 = float(str(val))
            n2 = float(str(cmp_val))
            if operator == 'gt':
                return n1 > n2
            if operator == 'gte':
                return n1 >= n2
            if operator == 'lt':
                return n1 < n2
            if operator == 'lte':
                return n1 <= n2
        except (ValueError, TypeError):
            return False

    if operator == 'contains':
        if val is None:
            return False
        return str(cmp_val or '').lower() in str(val).lower()

    if operator == 'starts_with':
        if val is None:
            return False
        return str(val).lower().startswith(str(cmp_val or '').lower())

    return False


@dataclass
class RuleEvaluationResult:
    triggered: bool
    action: str
    action_value: Optional[str] = None
    value: Any = None


def evaluate_rule(rule: LogicRule, ctx: Any) -> RuleEvaluationResult:
    """Evaluate a single logic rule against context."""
    if not rule.enabled:
        return RuleEvaluationResult(triggered=False, action=rule.action)

    val = resolve_property_value(rule.property, ctx)
    triggered = check_condition(val, rule.operator, rule.value)
    return RuleEvaluationResult(
        triggered=triggered,
        action=rule.action,
        action_value=rule.actionValue,
        value=val,
    )
