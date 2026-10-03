"""Tests for pure Python expressions engine and helpers."""
from eazyreport.expressions import (
    eval_condition,
    eval_template,
    eval_text,
    eval_value,
    format_currency,
    format_number,
    get_path,
    number_to_words,
)


def test_property_extraction():
    data = {
        'customer': {
            'name': 'Alice Smith',
            'address': {'city': 'Zurich', 'zip': 8001},
        },
        'items': [{'sku': 'A1', 'qty': 5}, {'sku': 'B2', 'qty': 10}],
    }
    assert get_path(data, 'customer.name') == 'Alice Smith'
    assert get_path(data, 'customer.address.city') == 'Zurich'
    assert get_path(data, 'customer.address.zip') == 8001
    assert get_path(data, 'items.0.sku') == 'A1'
    assert get_path(data, 'items.1.qty') == 10
    assert get_path(data, 'items.99.qty') is None
    assert get_path(data, 'nonexistent') is None


def test_format_helpers():
    ctx = {'price': 12450.5, 'date': '2026-10-02T12:00:00Z', 'ratio': 0.854}
    assert eval_text('{{formatCurrency price "USD" 2}}', ctx) == '$12,450.50'
    assert eval_text('{{formatNumber price 2 true}}', ctx) == '12,450.50'
    assert eval_text('{{formatPercent ratio 1}}', ctx) == '85.4%'
    assert eval_text('{{formatDate date "yyyy-MM-dd"}}', ctx) == '2026-10-02'


def test_math_and_aggregates():
    ctx = {
        'items': [
            {'price': 10, 'qty': 2},
            {'price': 20, 'qty': 1},
            {'price': 15, 'qty': 4},
        ]
    }
    assert eval_text('{{sum items "price"}}', ctx) == '45'
    assert eval_text('{{sum items "qty"}}', ctx) == '7'
    assert eval_text('{{count items}}', ctx) == '3'
    assert eval_text('{{avg items "price"}}', ctx) == '15'
    assert eval_text('{{add 10 5}}', ctx) == '15'
    assert eval_text('{{sub 20 8}}', ctx) == '12'
    assert eval_text('{{mul 4 5}}', ctx) == '20'
    assert eval_text('{{div 50 2}}', ctx) == '25'
    assert eval_text('{{round 14.567 2}}', ctx) == '14.57'


def test_string_helpers():
    ctx = {'name': '  john doe  ', 'code': 'abc123xyz'}
    assert eval_text('{{uppercase name}}', ctx) == '  JOHN DOE  '
    assert eval_text('{{trim name}}', ctx) == 'john doe'
    assert eval_text('{{titlecase (trim name)}}', ctx) == 'John Doe'
    assert eval_text('{{left code 3}}', ctx) == 'abc'
    assert eval_text('{{right code 3}}', ctx) == 'xyz'
    assert eval_text('{{padLeft 42 5 "0"}}', ctx) == '00042'
    assert eval_text('{{concat "Hello" " " "World"}}', ctx) == 'Hello World'


def test_logic_and_conditions():
    ctx = {'qty': 15, 'status': 'PAID', 'emptyList': []}
    assert eval_condition('gt qty 10', ctx) is True
    assert eval_condition('lt qty 10', ctx) is False
    assert eval_condition('eq status "PAID"', ctx) is True
    assert eval_condition('isEmpty emptyList', ctx) is True
    assert eval_text('{{iif (gt qty 10) "HIGH" "LOW"}}', ctx) == 'HIGH'
    assert eval_text('{{default emptyList "None"}}', ctx) == 'None'


def test_number_to_words():
    assert number_to_words(0) == 'Zero'
    assert number_to_words(42) == 'Forty-Two'
    assert number_to_words(125.50) == 'One Hundred Twenty-Five and 50/100'
    assert number_to_words(1000) == 'One Thousand'
    assert number_to_words(1234567.89) == (
        'One Million Two Hundred Thirty-Four Thousand Five Hundred Sixty-Seven and 89/100'
    )
