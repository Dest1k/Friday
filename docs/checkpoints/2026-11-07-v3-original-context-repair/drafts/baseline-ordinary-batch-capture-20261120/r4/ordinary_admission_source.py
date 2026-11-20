"""Compose one separately issued ordinary admission into the selected R4 source."""

import ast
import hashlib
import json
import re
from pathlib import PurePosixPath


SOURCE_SHA256 = "44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd"
AUTHORITY_SCHEMA = "frw.Root.ordinary-independent-history-admission.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def one(items, label):
    values = list(items)
    require(len(values) == 1, f"Exact {label} source position required")
    return values[0]


def exact_reference(reference):
    require(type(reference) is dict and set(reference) == {"path", "bytes", "sha256"},
            "Exact protected file reference required")
    path = reference["path"]
    require(type(path) is str and path.startswith("/") and not path.startswith("//")
            and path == str(PurePosixPath(path)) and ".." not in PurePosixPath(path).parts
            and "\0" not in path and path != "/"
            and type(reference["bytes"]) is int and reference["bytes"] > 0
            and type(reference["sha256"]) is str
            and re.fullmatch("[a-f0-9]{64}", reference["sha256"]),
            "Exact protected file reference required")


def compose_observer(source, *, run_id, scenario_sha256, authority, authority_ref,
                     checker_ref, proof_ref, contract_ref, prepare_ref):
    """Return private source for the existing owned caller. Does not issue authority."""
    require(type(source) is bytes and hashlib.sha256(source).hexdigest() == SOURCE_SHA256,
            "Exact reviewed R4 composition required")
    require(type(run_id) is str and re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id)
            and run_id != "jarvis-activate-check-01-r44"
            and type(scenario_sha256) is str and re.fullmatch("[a-f0-9]{64}", scenario_sha256),
            "Exact prospective run and scenario required")
    references = (authority_ref, checker_ref, proof_ref, contract_ref, prepare_ref)
    for reference in references:
        exact_reference(reference)
    require(len({reference["path"] for reference in references}) == len(references),
            "Separate Root evidence references required")
    require(type(authority) is dict and authority.get("schema") == AUTHORITY_SCHEMA
            and authority.get("operator") == "Root" and authority.get("accepted") is True
            and type(authority.get("authority_id")) is str and authority["authority_id"]
            and authority["authority_id"] != "ordinary-independent-jarvis-activate-20261108-r44"
            and authority.get("run_scenarios") == {run_id: scenario_sha256}
            and type(authority.get("history")) is dict and bool(authority["history"])
            and run_id not in authority["history"]
            and type(authority.get("ordered_predecessors", {})) is dict
            and set(authority.get("ordered_predecessors", {})) <= {run_id}
            and all(authority.get(key) is True for key in
                    ("new_independent_inputs_only", "no_old_task_replay"))
            and all(authority.get(key) is False for key in
                    ("new_trial_for_historical_task", "old_rows_modified",
                     "unknown_effects_resolved", "product_or_B00_acceptance")),
            "Exact singleton Root authority required")
    raw = (json.dumps(authority, ensure_ascii=True, sort_keys=True, allow_nan=False) + "\n").encode()
    require(len(raw) == authority_ref["bytes"]
            and hashlib.sha256(raw).hexdigest() == authority_ref["sha256"],
            "Root authority reference differs from canonical bytes")

    tree = ast.parse(source)
    runner = one((node for node in tree.body
                  if isinstance(node, ast.ClassDef) and node.name == "Runner"), "Runner")
    gate = one((node for node in runner.body if isinstance(node, ast.FunctionDef)
                and node.name == "ordinary_independent_admission"), "ordinary admission")
    lines = source.splitlines(keepends=True)
    edits = []
    for name, value in {"ORDINARY_INDEPENDENT_SCENARIOS": {run_id: scenario_sha256},
                        "ORDINARY_INDEPENDENT_AUTHORITY": authority_ref}.items():
        assignment = one((node for node in runner.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == name
                                  for target in node.targets)), name)
        edits.append((assignment.lineno, assignment.end_lineno, f"    {name} = {value!r}\n".encode()))
    previous_id = one((node for node in ast.walk(gate) if isinstance(node, ast.Constant)
                       and node.value == "ordinary-independent-jarvis-activate-20261108-r44"),
                      "previous authority ID")
    old_count = one((node.comparators[0] for node in ast.walk(gate) if isinstance(node, ast.Compare)
                     and ast.unparse(node) == "len(document['history']) != 40"), "history count")
    for node, value in ((previous_id, authority["authority_id"]), (old_count, len(authority["history"]))):
        line = lines[node.lineno - 1]
        patched = line[:node.col_offset] + repr(value).encode() + line[node.end_col_offset:]
        edits.append((node.lineno, node.end_lineno, patched))
    unmatched = one((node for node in gate.body if isinstance(node, ast.If)
                     and ast.unparse(node.test) == "expected_sha is None"), "unmatched admission")
    edits.append((unmatched.lineno, unmatched.end_lineno,
                  b"        if expected_sha is None:\n"
                  b"            raise Refused('Run outside the exact ordinary admission')\n"))
    end = gate.body[-1]
    require(isinstance(end, ast.Return) and ast.unparse(end.value) == "document",
            "Exact ordinary admission return required")
    check = f"""        import types as root_checker_types
        checker_ref = {checker_ref!r}
        checker_raw = safe_read(Path(checker_ref['path']))
        if len(checker_raw) != checker_ref['bytes'] or digest(checker_raw) != checker_ref['sha256']:
            raise Refused('Exact Root current checker bytes changed')
        checker = root_checker_types.ModuleType('_Root_baseline_current')
        checker.__file__ = checker_ref['path']
        exec(compile(checker_raw, checker.__file__, 'exec'), checker.__dict__)
        if checker.check({proof_ref!r}, contract_ref={contract_ref!r}, prepare_ref={prepare_ref!r},
                         run_id=name, scenario=scenario,
                         stage=getattr(self, '_send_phase', 'NEW')) is not True:
            raise Refused('Exact affirmative Root current qualification required')
        return document
"""
    edits.append((end.lineno, end.end_lineno, check.encode()))
    command = one((node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "main"), "observer command")
    edits.append((command.lineno, command.end_lineno,
                  b"def main(argv=None):\n"
                  b"    raise SystemExit('Ordinary admission requires the reviewed owned caller')\n"))
    entry = one((node for node in tree.body if isinstance(node, ast.If)
                 and ast.unparse(node.test) == "__name__ == '__main__'"), "observer entry point")
    edits.append((entry.lineno, entry.end_lineno,
                  b"if __name__ == '__main__':\n"
                  b"    main()\n"))

    previous = len(lines) + 1
    for first, last, replacement in sorted(edits, reverse=True):
        require(last < previous, "Ordinary admission source positions overlap")
        lines[first - 1:last] = [replacement]
        previous = first
    composed = b"".join(lines)
    compile(composed, "<bound ordinary observer>", "exec")
    return composed
