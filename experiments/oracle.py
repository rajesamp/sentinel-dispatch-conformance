"""Independent receipt oracle: no imports from gate, generations, or epochs.

The runner records immutable external approval state and revocation-at-enqueue.
This oracle compares actual sink receipts, not gate status or audit assertions.
"""
from __future__ import annotations

import json
import math
from typing import Any


def _object(pairs: list[tuple[str, Any]]) -> dict:
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON object key")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON number: " + value)


def decode_json(value: Any) -> Any:
    """Decode transport bytes independently; parsed fixture dictionaries also work."""
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = json.loads(value, object_pairs_hook=_object, parse_constant=_reject_constant)
    def validate(node: Any) -> None:
        kind = type(node)
        if node is None or kind in (bool, int):
            return
        if kind is float:
            if not math.isfinite(node):
                raise ValueError("non-finite JSON number")
        elif kind is str:
            node.encode("utf-8", errors="strict")
        elif kind is list:
            for child in node:
                validate(child)
        elif kind is dict:
            for key, child in node.items():
                if type(key) is not str:
                    raise ValueError("non-string JSON key")
                validate(key)
                validate(child)
        else:
            raise ValueError("not plain JSON")
    validate(value)
    return value


def equal_json(left: Any, right: Any) -> bool:
    """Typed structural equality; keys unordered, arrays ordered, bool != int."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(equal_json(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(equal_json(a, b) for a, b in zip(left, right))
    if type(left) not in (str, bool, int, float, type(None)):
        return False
    return left == right


def _field(record: dict, key: str) -> Any:
    if key + "_bytes" in record:
        return record[key + "_bytes"]
    return record[key]


def check_receipt(approval: dict | None, receipt: dict, *, revoked: bool = False) -> list[str]:
    """Return violations for one actual enqueue against an external approval.

    `revoked` must describe relevant revocation before THIS enqueue, never final
    state after the whole scenario. No epoch/generation field is consulted.
    """
    if approval is None:
        return ["dispatch_without_approval"]
    violations = []
    if revoked:
        violations.append("dispatch_after_relevant_revocation")
    if receipt.get("server") != approval.get("server"):
        violations.append("server_mismatch")
    if receipt.get("connection") != approval.get("connection"):
        violations.append("connection_mismatch")
    for key in ("descriptor", "request"):
        try:
            expected, actual = decode_json(_field(approval, key)), decode_json(_field(receipt, key))
            if not equal_json(expected, actual):
                violations.append(key + "_mismatch")
        except (ValueError, TypeError, UnicodeError, KeyError, RecursionError):
            violations.append("invalid_" + key + "_receipt")
    return violations


def evaluate_receipts(approval: dict | None, receipts: list[dict], *,
                      revoked: bool = False, expected_policy: str | None = None,
                      expected_receipt: dict | None = None,
                      expected_dispatch_count: int | None = None) -> dict:
    """Evaluate safety and declared scenario completion independently.

    Each receipt may carry `revoked_at_dispatch` and `approval` snapshots; these
    override final defaults and are essential when events follow an enqueue.
    A missing expected dispatch is an outcome/availability failure, not an
    invariant violation. An extra dispatch violates single-use approval.
    """
    violations = []
    for index, receipt in enumerate(receipts):
        active_approval = receipt.get("approval", approval)
        active_revocation = receipt.get("revoked_at_dispatch", revoked)
        for issue in check_receipt(active_approval, receipt, revoked=active_revocation):
            violations.append({"receipt_index": index, "issue": issue})
    # Each scenario authorizes one final operation; a reapproval replaces, rather
    # than adds to, its intended dispatch. General multi-approval traces need a
    # per-approval cardinality contract and are outside this helper's scope.
    if len(receipts) > 1:
        violations.append({"receipt_index": 1, "issue": "single_use_approval_replayed"})
    outcome_issues = []
    if expected_dispatch_count is None and expected_policy is not None:
        expected_dispatch_count = 0 if expected_policy == "deny" else 1
    if expected_dispatch_count is not None and len(receipts) != expected_dispatch_count:
        outcome_issues.append("dispatch_count_differs_from_declared_policy")
    if expected_receipt is not None:
        for index, receipt in enumerate(receipts):
            for issue in check_receipt(expected_receipt, receipt):
                outcome_issues.append(f"receipt_{index}_expected_{issue}")
    return {"safe": not violations,
            "policy_satisfied": not outcome_issues,
            "violations": violations, "outcome_issues": outcome_issues,
            "dispatch_count": len(receipts)}
