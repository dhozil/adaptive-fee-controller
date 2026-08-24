"""Direct-mode tests for the AdaptiveFeeController contract.

Covers: profile creation validation, owner-only fee adjustment, consensus on
the accepted fee value (tight tolerance), pause/resume gating, and the validator
agreeing on the same accepted value that is stored.
"""

import json
import re

from gltest.direct import create_address

PROFILE = {
    "name": "DEX Trading Fee",
    "protocol": "Uniswap V3",
    "fee_type": "dynamic",
    "base_fee": 30,
    "min_fee": 10,
    "max_fee": 100,
    "adjustment_step": 5,
}

MARKET = "High volatility, elevated on-chain volume, deeper liquidity."
FEE_JSON = json.dumps(
    {"new_fee": 35, "adjustment_reason": "Volatility requires a modest fee rise.", "market_summary": "Elevated activity.", "confidence": 80}
)


def _create(contract, vm, owner, profile=PROFILE):
    vm.sender = owner
    return contract.create_fee_profile(**profile)


def test_create_profile_validates_bounds(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/adaptive_fee_controller.py")
    owner = create_address("owner")

    direct_vm.sender = owner
    with direct_vm.expect_revert("Min fee cannot exceed max fee"):
        contract.create_fee_profile("T", "P", "dynamic", 10, 20, 10, 1)
    with direct_vm.expect_revert("step"):
        contract.create_fee_profile("T", "P", "dynamic", 5, 1, 100, 0)

    pid = _create(contract, direct_vm, owner)
    assert contract.get_profile(pid)["current_fee"] == PROFILE["base_fee"]


def test_adjust_fee_owner_only(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/adaptive_fee_controller.py")
    owner = create_address("owner")
    other = create_address("other")
    pid = _create(contract, direct_vm, owner)

    # A stranger cannot move someone else's fee.
    direct_vm.sender = other
    with direct_vm.expect_revert("Only the profile owner"):
        contract.adjust_fee(pid, MARKET)

    direct_vm.mock_llm(re.escape("adaptive fee controller"), FEE_JSON)
    direct_vm.sender = owner
    result = contract.adjust_fee(pid, MARKET)
    assert result["new_fee"] == 35
    assert contract.get_profile(pid)["current_fee"] == 35


def test_adjust_fee_respects_bounds(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/adaptive_fee_controller.py")
    owner = create_address("owner")
    pid = _create(contract, direct_vm, owner)

    out_of_range = json.dumps({"new_fee": 99, "adjustment_reason": "way out", "market_summary": "boom"})
    direct_vm.mock_llm(re.escape("adaptive fee controller"), out_of_range)
    direct_vm.sender = owner
    result = contract.adjust_fee(pid, MARKET)
    assert result["new_fee"] <= PROFILE["max_fee"]
    assert result["new_fee"] >= PROFILE["min_fee"]
    # 99 is > step (5) away from base 30 -> must be clamped back to current
    assert result["new_fee"] == PROFILE["base_fee"]


def test_pause_blocks_adjustment(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/adaptive_fee_controller.py")
    owner = create_address("owner")
    other = create_address("other")
    pid = _create(contract, direct_vm, owner)

    direct_vm.sender = other
    with direct_vm.expect_revert("Only owner can pause"):
        contract.pause_profile(pid)

    direct_vm.sender = owner
    contract.pause_profile(pid)
    with direct_vm.expect_revert("not active"):
        contract.adjust_fee(pid, MARKET)

    contract.resume_profile(pid)


def test_validator_agrees_on_accepted_fee(direct_vm, direct_deploy):
    """The captured validator must accept exactly the encoded leader result."""
    contract = direct_deploy("contracts/adaptive_fee_controller.py")
    owner = create_address("owner")
    pid = _create(contract, direct_vm, owner)

    direct_vm.mock_llm(re.escape("adaptive fee controller"), FEE_JSON)
    direct_vm.sender = owner
    result = contract.adjust_fee(pid, MARKET)
    assert result["new_fee"] == 35

    # Validator accepts the exact leader fee (35), rejects a materially different one.
    ok = direct_vm.run_validator(leader_result={"new_fee": 35}, index=-1)
    assert ok is True
    bad = direct_vm.run_validator(leader_result={"new_fee": 40}, index=-1)
    # diff 5 bp > tolerance 1 bp (and > step 5 check) -> reject
    assert bad is False