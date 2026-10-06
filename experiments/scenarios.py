"""Declarative, finite challenge suite; not a statistical attack sample.

Generated independently of the gate implementation's return decisions. All
expected policy outcomes follow the contract recorded in research/holdout-plan.md.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


BASE_TOOL = {
    "name": "read_file",
    "description": "Read fixture.",
    "inputSchema": {"type": "object", "properties": {}},
}
BASE_ARGUMENTS = {"path": "fixture.txt"}


def tool(**updates: Any) -> dict:
    result = deepcopy(BASE_TOOL)
    result.update(deepcopy(updates))
    return result


def catalog(server: str = "server-a", tools: list | None = None,
            connection: str = "c1") -> dict:
    return {"server": server, "connection": connection,
            "tools": deepcopy([BASE_TOOL] if tools is None else tools)}


def request(arguments: dict | None = None, name: str = "read_file") -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": deepcopy(
                BASE_ARGUMENTS if arguments is None else arguments)}}


def refresh(tools: list, *, at: str = "after_prepare", server: str = "server-a",
            connection: str = "c1", revokes: bool = False) -> dict:
    return {"at": at, "action": "refresh", "server": server,
            "connection": connection, "tools": deepcopy(tools),
            "revokes_approval": revokes}


def complete(tag: str, tools: list, *, revokes: bool = False,
             server: str = "server-a", connection: str = "c1") -> dict:
    return {"at": "after_prepare", "action": "complete_refresh", "tag": tag,
            "server": server, "connection": connection,
            "tools": deepcopy(tools), "revokes_approval": revokes}


def begin(tag: str, server: str = "server-a") -> dict:
    return {"at": "after_prepare", "action": "begin_refresh", "tag": tag,
            "server": server, "revokes_approval": False}


def mutate_args(path: list, value: Any, *, at: str = "after_prepare") -> dict:
    return {"at": at, "action": "mutate_args", "path": path,
            "value": deepcopy(value), "revokes_approval": False}


def mutate_source(path: list, value: Any, *, at: str = "after_prepare",
                  catalog_index: int = 0, tool_index: int = 0) -> dict:
    return {"at": at, "action": "mutate_source", "path": path,
            "value": deepcopy(value), "catalog_index": catalog_index,
            "tool_index": tool_index, "revokes_approval": False}


def reapprove() -> dict:
    return {"at": "after_prepare", "action": "reapprove",
            "revokes_approval": False, "resets_revocation": True}


def apply_mutation(target: dict | list, path: list, value: Any) -> None:
    """Mutate a caller-owned fixture; refresh is a separate explicit operation."""
    if not path:
        raise ValueError("mutation path must name a field")
    node = target
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = deepcopy(value)


def _case(identifier: str, family: str, *, operations: list | None = None,
          split: str = "development", kind: str = "challenge",
          policy: str = "allow", catalogs: list | None = None,
          selected: dict | None = None, arguments: dict | None = None,
          expected_tool: dict | None = None, expected_args: dict | None = None,
          expected_connection: str = "c1", notes: str = "") -> dict:
    selection = deepcopy(selected or {"server": "server-a", "name": "read_file"})
    args = deepcopy(BASE_ARGUMENTS if arguments is None else arguments)
    expected = None if policy == "deny" else {
        "server": selection["server"], "connection": expected_connection,
        "descriptor": deepcopy(BASE_TOOL if expected_tool is None else expected_tool),
        "request": request(args if expected_args is None else expected_args,
                           selection["name"]),
    }
    return {
        "id": identifier, "family": family, "split": split, "kind": kind,
        "initial_catalogs": deepcopy([catalog()] if catalogs is None else catalogs),
        "selection": selection, "arguments": args,
        "operations": deepcopy(operations or []), "expected_policy": policy,
        "expected_receipt": expected,
        "expected_dispatch_count": 0 if policy == "deny" else 1,
        "notes": notes,
    }


def generate_cases() -> list[dict]:
    """Return fresh fixtures. This is a challenge suite, not exhaustive traces."""
    changed = tool(description="Read revised fixture.")
    sibling = tool(name="list_files", description="List fixtures.")
    schema = tool(inputSchema={"type": "object", "properties": {
        "path": {"type": "string", "description": "Approved path only."}}})
    reordered = {"inputSchema": {"properties": {}, "type": "object"},
                 "description": "Read fixture.", "name": "read_file"}
    nested_args = {"path": "fixture.txt", "options": {"fields": ["name", "size"]}}
    rich = tool(title="Reader", annotations={"readOnlyHint": True},
                outputSchema={"type": "object", "properties": {}},
                _meta={"labels": ["first", "second"]})
    swapped_rich = deepcopy(rich)
    swapped_rich["_meta"]["labels"] = ["second", "first"]
    return [
        _case("dev-normal", "normal", kind="benign",
              notes="Unchanged operation must reach the sink once."),
        _case("dev-server-namespace", "identity", catalogs=[catalog(), catalog("server-b")],
              notes="Identical tool names and bytes do not make host server identities interchangeable."),
        _case("dev-identical-refresh", "benign-refresh", kind="benign",
              operations=[refresh([BASE_TOOL])]),
        _case("dev-reordered-json", "benign-equivalence", kind="benign",
              operations=[refresh([reordered])],
              notes="Object key order alone does not revoke the selected operation."),
        _case("dev-unrelated-server", "benign-isolation", kind="benign",
              operations=[refresh([changed], server="server-b")]),
        _case("dev-unrelated-tool", "benign-isolation", kind="benign",
              operations=[refresh([BASE_TOOL, sibling])]),
        _case("dev-catalog-order", "benign-equivalence", kind="benign",
              catalogs=[catalog(tools=[BASE_TOOL, sibling])],
              operations=[refresh([sibling, BASE_TOOL])]),
        _case("dev-source-copy", "copy-boundary",
              operations=[mutate_source(["description"], "Caller changed its own dictionary.")],
              notes="An unpublished caller-owned mutation must not change the admitted or dispatched snapshot."),
        _case("dev-stale-selection", "selection-to-approval", policy="deny",
              operations=[refresh([changed], at="after_select", revokes=True)],
              notes="The selected descriptor is withdrawn before prepare; no fresh approval is given."),
        _case("dev-description-refresh", "descriptor-revocation", policy="deny",
              operations=[refresh([changed], revokes=True)]),
        _case("dev-schema-refresh", "descriptor-revocation", policy="deny",
              operations=[refresh([schema], revokes=True)]),
        _case("dev-title-refresh", "complete-metadata", policy="deny",
              operations=[refresh([tool(title="Revised reader")], revokes=True)]),
        _case("dev-annotations-refresh", "complete-metadata", policy="deny",
              operations=[refresh([tool(annotations={"readOnlyHint": False})], revokes=True)]),
        _case("dev-output-schema-refresh", "complete-metadata", policy="deny",
              operations=[refresh([tool(outputSchema={"type": "array"})], revokes=True)]),
        _case("dev-extension-refresh", "complete-metadata", policy="deny",
              operations=[refresh([tool(_meta={"routing": {"region": "revised"}})], revokes=True)]),
        _case("dev-tool-removal", "explicit-withdrawal", policy="deny",
              operations=[refresh([], revokes=True)]),
        _case("dev-connection-refresh", "connection-revocation", policy="deny",
              operations=[refresh([BASE_TOOL], connection="c2", revokes=True)]),
        _case("dev-remove-readd", "aba-revocation", policy="deny",
              operations=[refresh([], revokes=True), refresh([BASE_TOOL], revokes=True)],
              notes="Restoring equal bytes does not restore an approval revoked by withdrawal."),
        _case("dev-description-aba", "aba-revocation", policy="deny",
              operations=[refresh([changed], revokes=True), refresh([BASE_TOOL], revokes=True)],
              notes="A revoked approval remains revoked after a change-and-revert."),
        _case("dev-mutable-arguments", "request-snapshot",
              operations=[mutate_args(["path"], "different.txt")],
              notes="The original approved request, not the later caller dictionary, is dispatched."),
        _case("dev-single-use", "permit-replay", policy="allow_once",
              operations=[{"at": "after_execute", "action": "execute_again",
                           "revokes_approval": False}],
              notes="The same single-use approval may produce only one dispatch receipt."),
        _case("dev-clean-recovery", "legitimate-reapproval", kind="benign",
              operations=[refresh([changed], revokes=True), reapprove()], expected_tool=changed),
        _case("dev-argument-reapproval", "legitimate-reapproval", kind="benign",
              operations=[mutate_args(["path"], "authorized-new.txt"), reapprove()],
              expected_args={"path": "authorized-new.txt"}),
        _case("dev-outoforder-refresh", "refresh-order",
              operations=[begin("older"), begin("newer"), complete("newer", [BASE_TOOL]),
                          complete("older", [changed])],
              notes="The stale older completion cannot publish or revoke the unchanged latest-requested catalogue."),
        _case("verify-isolation-plus-arguments", "composition-isolation-snapshot", split="verification",
              operations=[refresh([changed], server="server-b"), mutate_args(["path"], "other.txt")]),
        _case("verify-namespace-source-copy", "composition-identity-copy", split="verification",
              catalogs=[catalog(), catalog("server-b")],
              operations=[refresh([changed], server="server-b"),
                          mutate_source(["inputSchema", "properties"], {"injected": {"type": "string"}})]),
        _case("verify-selection-aba", "composition-selection-aba", split="verification", policy="deny",
              operations=[refresh([changed], at="after_select", revokes=True),
                          refresh([BASE_TOOL], at="after_select", revokes=True)]),
        _case("verify-connection-aba", "composition-connection-aba", split="verification", policy="deny",
              operations=[refresh([BASE_TOOL], connection="c2", revokes=True),
                          refresh([BASE_TOOL], connection="c1", revokes=True)]),
        _case("verify-remove-readd-reapprove", "composition-recovery", split="verification", kind="benign",
              operations=[refresh([], revokes=True), refresh([BASE_TOOL], revokes=True), reapprove()]),
        _case("verify-newer-change-stale-restore", "composition-refresh-revocation", split="verification",
              policy="deny", operations=[begin("older"), begin("newer"),
                                         complete("newer", [changed], revokes=True),
                                         complete("older", [BASE_TOOL])],
              notes="The stale older result must not resurrect an approval revoked by the accepted newer result."),
        _case("verify-stale-change-nested-args", "composition-refresh-snapshot", split="verification",
              arguments=nested_args,
              operations=[begin("older"), begin("newer"), complete("newer", [BASE_TOOL]),
                          complete("older", [changed]), mutate_args(["options", "fields", 0], "secret")]),
        _case("verify-extension-array-order", "composition-rich-descriptor", split="verification",
              policy="deny", catalogs=[catalog(tools=[rich])],
              operations=[refresh([swapped_rich], revokes=True)],
              notes="Array order is preserved in the full descriptor contract; semantic schema equivalence is not assumed."),
        _case("verify-nested-source-copy", "composition-rich-copy", split="verification",
              catalogs=[catalog(tools=[rich])], expected_tool=rich,
              operations=[mutate_source(["_meta", "labels", 0], "changed"),
                          refresh([sibling], server="server-b")]),
        _case("verify-reconnect-reapprove", "composition-connection-recovery", split="verification", kind="benign",
              operations=[refresh([BASE_TOOL], connection="c2", revokes=True), reapprove()],
              expected_connection="c2"),
        _case("verify-after-enqueue-refresh", "ordering-after-dispatch", split="verification", kind="benign",
              operations=[refresh([changed], at="after_execute", revokes=True)],
              notes="A later refresh cannot retroactively invalidate a correctly enqueued request."),
        _case("verify-two-safe-refreshes-replay", "composition-safe-refresh-replay", split="verification",
              policy="allow_once", operations=[refresh([reordered]), refresh([BASE_TOOL, sibling]),
                  {"at": "after_execute", "action": "execute_again", "revokes_approval": False}],
              notes="Harmless refreshes preserve the operation but do not reset single-use consumption."),
    ]


def manifest() -> dict:
    return {"schema_version": 1,
            "scope": "declarative finite challenge suite; not exhaustive enumeration or independent statistical samples",
            "connection_default": "c1", "request_id": 1,
            "cases": generate_cases()}


if __name__ == "__main__":
    import json
    print(json.dumps(manifest(), indent=2, ensure_ascii=False))
