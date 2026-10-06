"""Enumerate all words of length <=3 over a declared six-event host model.

This finite model is deliberately smaller than MCP. Expected revocation follows
the selected-operation contract, without importing any implementation or oracle.
No language model, network service, or malicious payload is executed.
"""
from __future__ import annotations

from copy import deepcopy
import itertools
import json

ALPHABET = ("publish_original", "publish_changed", "withdraw",
            "reconnect", "unrelated_server", "mutate_arguments")
BASE = {"name": "read_file", "description": "Read fixture.",
        "inputSchema": {"type": "object", "properties": {}}}
CHANGED = dict(BASE, description="Read revised fixture.")
ARGS = {"path": "fixture.txt"}


def generate(depth: int = 3) -> dict:
    if type(depth) is not int or not 0 <= depth <= 4:
        raise ValueError("depth must be 0..4")
    cases = []
    for length in range(depth + 1):
        for word in itertools.product(ALPHABET, repeat=length):
            state = ("original", "c1")
            revoked = False
            operations = []
            for event in word:
                next_state = state
                op = {"at": "after_prepare", "revokes_approval": False}
                if event == "mutate_arguments":
                    op.update(action="mutate_args", path=["path"], value="mutated.txt")
                elif event == "unrelated_server":
                    op.update(action="refresh", server="server-b", connection="b1",
                              tools=[deepcopy(CHANGED)])
                else:
                    if event == "publish_original":
                        next_state = ("original", "c1")
                    elif event == "publish_changed":
                        next_state = ("changed", "c1")
                    elif event == "withdraw":
                        next_state = None
                    elif event == "reconnect":
                        next_state = ("original", "c2")
                    tools = ([] if next_state is None else
                             [deepcopy(BASE if next_state[0] == "original" else CHANGED)])
                    op.update(action="refresh", server="server-a",
                              connection="c1" if next_state is None else next_state[1],
                              tools=tools)
                    # An observed change/withdrawal of the approved binding revokes
                    # that approval permanently, even if the original later returns.
                    op["revokes_approval"] = state != next_state
                    revoked = revoked or op["revokes_approval"]
                    state = next_state
                operations.append(op)
            receipt = None if revoked else {
                "server": "server-a", "connection": "c1", "descriptor": deepcopy(BASE),
                "request": {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "read_file", "arguments": deepcopy(ARGS)}},
            }
            cases.append({
                "id": "enum-" + ("__".join(word) if word else "empty"),
                "family": "finite-traces-length-" + str(length),
                "split": "bounded_enumeration", "kind": "challenge",
                "initial_catalogs": [{"server": "server-a", "connection": "c1",
                                      "tools": [deepcopy(BASE)]}],
                "selection": {"server": "server-a", "name": "read_file"},
                "arguments": deepcopy(ARGS), "operations": operations,
                "expected_policy": "deny" if revoked else "allow",
                "expected_receipt": receipt,
                "expected_dispatch_count": 0 if revoked else 1,
                "notes": "Designed finite trace, not an independent attack sample.",
            })
    return {"schema_version": 1, "scope": "all finite words over declared event alphabet",
            "alphabet": list(ALPHABET), "maximum_length": depth,
            "expected_count": sum(len(ALPHABET)**n for n in range(depth + 1)),
            "connection_default": "c1", "request_id": 1, "cases": cases}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, ensure_ascii=False))
