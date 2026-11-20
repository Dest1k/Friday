"""Select the reviewed ordinary guard with the exact D12 timing profile."""

from hashlib import sha256
import json


CURRENT_SHA256 = "2983e06dc5579adae0f0983d64d07b65c41f849b03dca0985f270d2547a9411b"
SCENARIO_SHA256 = "3526cfe50aaf7318843a8a4b148b0df8ab0cc304328c6401fa20477fa62fc121"


def compose_current(source, scenario):
    """Return a private guard for the exact 900-second plan with 600 seconds of capture."""
    if type(source) is not bytes or sha256(source).hexdigest() != CURRENT_SHA256:
        raise ValueError("Exact reviewed ordinary current guard required")
    canonical = (json.dumps(scenario, ensure_ascii=True, sort_keys=True, allow_nan=False) + "\n").encode()
    if sha256(canonical).hexdigest() != SCENARIO_SHA256:
        raise ValueError("Exact prepared D12 scenario required")

    # Keep the existing 300-second margin between the tester deadline and the
    # owned supervisor. Neither clock exists until the ordinary caller starts it.
    original = (b"TIMING = dict(operation_seconds=300, reply_window_seconds=180, ack_seconds=10,\n"
                b"              reserve_seconds=5, outer_seconds=600)\n")
    selected = (b"TIMING = dict(operation_seconds=900, reply_window_seconds=600, ack_seconds=10,\n"
                b"              reserve_seconds=5, outer_seconds=1200)\n")
    pin = SCENARIO_SHA256.encode("ascii")
    gate = b"    scenario_sha = digest(encoded(scenario))\n"
    wire = b"    proof = document(proof_ref)\n"
    edits = (
        (original, selected),
        (gate, gate + b"    require(scenario_sha == '" + pin + b"', 'Exact D12 current scenario required')\n"),
        (wire, b"    require(digest(encoded(run['scenario'])) == run['scenario_sha256'] == '" + pin
         + b"', 'Exact D12 wire scenario required')\n" + wire),
    )
    for anchor, replacement in edits:
        if source.count(anchor) != 1:
            raise ValueError("Exact D12 ordinary guard source position required")
        source = source.replace(anchor, replacement, 1)
    compile(source, "<selected D12 current guard>", "exec")
    return source
