"""Lab 6 - Branch coverage tests for coffee_shop_order.py

Goal: make every decision evaluate both True and False (and every loop
both enter and exit). Includes the line-coverage tests, plus the
"other side" of each condition and boundary values.
Run:  coverage run --branch -m pytest BranchCoverageTest_coffee_shop_order.py
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


# ---------- process_order_batch: input validation (line 2, both halves of `or`) ----------

def test_single_medium_coffee():
    orders = [make_order(customizations=[{"type": "standard", "cost": 0.5}])]
    result = process_order_batch(orders, 0.1)
    assert result["total"] == 5.5
    assert result["status"] == "COMPLETED"


def test_non_list_orders_raises():
    with pytest.raises(ValueError):
        process_order_batch("not a list", 0.1)


def test_negative_tax_rate_raises():
    with pytest.raises(ValueError):
        process_order_batch([make_order()], -0.01)


def test_zero_tax_rate_is_valid():                  # boundary: tax_rate == 0
    assert process_order_batch([make_order()], 0.0)["total"] == 4.5


def test_empty_list_gives_no_sale():                # loop at line 8 never entered
    assert process_order_batch([], 0.1) == {"total": 0.0, "status": "NO_SALE"}


# ---------- paid check (line 9) ----------

def test_unpaid_order_is_skipped():
    orders = [make_order(paid=False), make_order()]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_missing_paid_key_defaults_to_unpaid():
    order = make_order()
    del order["paid"]
    assert process_order_batch([order], 0.0)["status"] == "NO_SALE"


# ---------- size chain (lines 13, 15, 17, 19) ----------

@pytest.mark.parametrize("size, expected", [("small", 3.0), ("medium", 4.5), ("large", 6.0)])
def test_each_valid_size_price(size, expected):
    assert process_order_batch([make_order(size=size)], 0.0)["total"] == expected


def test_missing_size_defaults_to_medium():
    order = make_order()
    del order["size"]
    assert process_order_batch([order], 0.0)["total"] == 4.5


def test_unknown_size_is_rejected_and_skipped():
    result = process_order_batch([make_order(size="huge"), make_order()], 0.0)
    assert result["total"] == 4.5
    assert result["status"] == "COMPLETED"


# ---------- customizations loop and branches (lines 26-42) ----------

def test_no_customizations_loop_skipped():
    assert process_order_batch([make_order(customizations=[])], 0.0)["total"] == 4.5


def test_missing_customizations_key_defaults_to_empty():
    order = make_order()
    del order["customizations"]
    assert process_order_batch([order], 0.0)["total"] == 4.5


def test_negative_cost_is_rejected_not_added():             # line 30 True
    orders = [make_order(customizations=[{"type": "standard", "cost": -1.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_zero_cost_is_not_rejected():                       # line 30 boundary
    orders = [make_order(customizations=[{"type": "standard", "cost": 0.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_other_type_adds_full_cost():                       # line 41 else
    orders = [make_order(customizations=[{"type": "oat_milk", "cost": 0.7}])]
    assert process_order_batch(orders, 0.0)["total"] == pytest.approx(5.2)


def test_missing_type_and_cost_use_defaults():              # .get defaults on 27-28
    orders = [make_order(customizations=[{}])]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_syrup_under_cap_adds_full_cost():                  # line 40 True side
    orders = [make_order(customizations=[{"type": "syrup", "cost": 1.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 5.5


def test_syrup_exactly_at_cap_adds_full_cost():             # boundary cost == 1.5
    orders = [make_order(customizations=[{"type": "syrup", "cost": 1.5}])]
    assert process_order_batch(orders, 0.0)["total"] == 6.0


def test_syrup_over_cap_is_capped():                        # line 40 False side
    orders = [make_order(customizations=[{"type": "syrup", "cost": 3.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 6.0


def test_allergen_alert_not_strict_keeps_item_but_counts_rejection():  # line 36 False
    orders = [make_order(customizations=[
        {"type": "allergen_alert", "cost": 0.0},
        {"type": "standard", "cost": 0.5}])]                # loop continues after alert
    result = process_order_batch(orders, 0.0)
    assert result == {"total": 5.0, "status": "COMPLETED"}


def test_allergen_alert_strict_zeroes_item_and_breaks():    # line 36 True + break
    orders = [make_order(strict_allergy=True, customizations=[
        {"type": "allergen_alert", "cost": 0.0},
        {"type": "standard", "cost": 9.0}])]                # must never be added
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


# ---------- membership (line 44) ----------

def test_member_discount_applied():
    result = process_order_batch([make_order(is_member=True)], 0.0)
    assert result["total"] == pytest.approx(4.05)


def test_non_member_no_discount():
    assert process_order_batch([make_order(is_member=False)], 0.0)["total"] == 4.5


# ---------- final status (lines 51, 53) ----------

def test_exactly_four_rejections_is_not_audit():            # boundary: 4 > 4 is False
    orders = [make_order(size="huge") for _ in range(4)] + [make_order()]
    result = process_order_batch(orders, 0.0)
    assert result["status"] == "COMPLETED"


def test_five_rejections_is_audit_rejected():               # boundary: 5 > 4 is True
    orders = [make_order(size="huge") for _ in range(5)] + [make_order()]
    result = process_order_batch(orders, 0.0)
    assert result == {"total": 4.5, "status": "AUDIT_REJECTED"}


def test_tax_is_applied_and_rounded():
    result = process_order_batch([make_order()], 0.0825)    # 4.5 * 1.0825 = 4.87125
    assert result["total"] == 4.87


# ---------- check_espresso_machine ----------

def test_none_or_empty_returns_no_data():
    assert check_espresso_machine([]) == "NO_DATA"
    assert check_espresso_machine(None) == "NO_DATA"


def test_all_normal_is_optimal():
    assert check_espresso_machine([[90.0, 92.0, 94.0], [91.0]]) == "OPTIMAL"


def test_empty_cycle_inside_list_is_optimal():              # inner loop never entered
    assert check_espresso_machine([[]]) == "OPTIMAL"


def test_two_consecutive_overheats_shutdown():
    assert check_espresso_machine([[95.0, 97.0, 98.0]]) == "SHUTDOWN"


def test_single_overheat_is_not_enough():                   # streak 1, no shutdown
    assert check_espresso_machine([[97.0, 90.0]]) == "OPTIMAL"


def test_non_consecutive_overheats_reset_streak():          # else branch resets streak
    assert check_espresso_machine([[97.0, 90.0, 97.0, 90.0]]) == "OPTIMAL"


def test_exactly_96_is_not_overheating():                   # boundary: 96.0 > 96.0 False
    assert check_espresso_machine([[96.0, 96.0, 96.0]]) == "OPTIMAL"


def test_streak_resets_between_cycles():                    # streak is per cycle
    assert check_espresso_machine([[97.0], [97.0]]) == "OPTIMAL"


def test_shutdown_found_in_later_cycle():
    assert check_espresso_machine([[90.0], [97.0, 98.0]]) == "SHUTDOWN"
