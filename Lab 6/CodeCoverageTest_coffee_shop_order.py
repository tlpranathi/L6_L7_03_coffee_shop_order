"""Lab 6 - Code (line) coverage tests for coffee_shop_order.py

Goal: execute every statement in the module at least once.
Run:  coverage run -m pytest CodeCoverageTest_coffee_shop_order.py
      coverage report -m
"""
import pytest
from coffee_shop_order import process_order_batch, check_espresso_machine


def make_order(**overrides):
    """Build a paid, medium, non-member order; override any field per test."""
    order = {"paid": True, "size": "medium", "is_member": False,
             "strict_allergy": False, "customizations": []}
    order.update(overrides)
    return order


# ---------- process_order_batch ----------

def test_single_medium_coffee():
    orders = [make_order(customizations=[{"type": "standard", "cost": 0.5}])]
    result = process_order_batch(orders, 0.1)
    assert result["total"] == 5.5
    assert result["status"] == "COMPLETED"


def test_invalid_orders_type_raises():                      # line 3
    with pytest.raises(ValueError):
        process_order_batch("not a list", 0.1)


def test_unpaid_order_is_skipped_gives_no_sale():           # lines 10, 54
    result = process_order_batch([make_order(paid=False)], 0.1)
    assert result == {"total": 0.0, "status": "NO_SALE"}


def test_small_and_large_sizes():                           # lines 14, 18
    orders = [make_order(size="small"), make_order(size="large")]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 9.0                           # 3.0 + 6.0
    assert result["status"] == "COMPLETED"


def test_unknown_size_is_rejected():                        # lines 20-21
    result = process_order_batch([make_order(size="huge"), make_order()], 0.0)
    assert result["total"] == 4.5                           # only the medium counts
    assert result["status"] == "COMPLETED"


def test_negative_customization_cost_is_rejected():         # lines 31-32
    orders = [make_order(customizations=[{"type": "standard", "cost": -1.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 4.5


def test_strict_allergy_zeroes_the_item():                  # lines 35-38
    orders = [make_order(strict_allergy=True,
                         customizations=[{"type": "allergen_alert", "cost": 0.0}])]
    result = process_order_batch(orders, 0.1)
    assert result == {"total": 0.0, "status": "NO_SALE"}


def test_syrup_cost_is_capped_at_1_50():                    # line 40
    orders = [make_order(customizations=[{"type": "syrup", "cost": 2.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 6.0                           # 4.5 + 1.5 cap


def test_member_gets_ten_percent_off():                     # line 45
    result = process_order_batch([make_order(is_member=True)], 0.0)
    assert result["total"] == pytest.approx(4.05)           # 4.5 * 0.9


def test_more_than_four_rejections_triggers_audit():        # line 52
    orders = [make_order(size="huge") for _ in range(5)]
    result = process_order_batch(orders, 0.0)
    assert result["status"] == "AUDIT_REJECTED"


# ---------- check_espresso_machine ----------

def test_no_data_returns_no_data():                         # line 60
    assert check_espresso_machine([]) == "NO_DATA"


def test_two_consecutive_overheats_shutdown():              # lines 62-68
    assert check_espresso_machine([[95.0, 97.0, 98.0]]) == "SHUTDOWN"


def test_normal_temperatures_are_optimal():                 # lines 69-71
    assert check_espresso_machine([[90.0, 92.0, 94.0]]) == "OPTIMAL"
