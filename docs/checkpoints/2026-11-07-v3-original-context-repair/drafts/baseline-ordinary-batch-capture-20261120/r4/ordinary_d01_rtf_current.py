"""Observe the exact RTF preparation on the selected Core296 ordinary route."""

from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import re
import sys

SCENARIO = "45e1732b0d49020182a3a9f2d67056b8c11d9c0f314240de077eb6fd19a13641"
SOURCE = "008f55eddd87fe35f7a40413d97eecba9a293d2029db9a32420d0973001b3535"
DISPLAY_NAME = "D01-Shlyuz-Serebryanoy-kosy-SK-D01-683.rtf"
PREPARATION = "f95f962ff2b80e787fd3b254b14cc5a4fbd97cdb3846bb3787c05ff54d36e8f9"
PINS_CORE_RECEIPT = "130684bfc13b4836c31de18da3b372939e598db2c4b1a602f95e8f90e4722a77"
PINS = {
    "core": "995e78aa4956db7ff67abe84691e92e1467353ae2bd37007dcb905b0c2df54f2",
    "native": "bd465b9664851e061b7a1ea69ed01a53d0fd40b075c7664d394c855e548b45b1",
    "pairing": "ac30ed03842e37eb6844321187ad6f0d7e8c03096bc0c38e031a6f4ba014e0f8",
    "route": "e7360483db530bfb47da5e871dc4774341dd06831c2071755818a29bd462174d",
    "reader": "094d85ed1417f7e61f2e3c483cdd5ed733496fbffc5017f3d66434931dcc929c",
}
ROUTE_ROLES = (
    "gateway/ordinary_turn_projection.py",
    "gateway/pairing.py",
    "gateway/admitted_ingress.py",
    "gateway/platforms/base.py",
    "gateway/run_attachment_presentation.py",
    "gateway/run_plugin_delivery.py",
    "gateway/run_inbound_media.py",
    "hermes_cli/config.py",
    "hermes_cli/friday_product_access.py",
    "hermes_cli/friday_user_scope.py",
    "hermes_cli/plugins_state.py",
    "plugins/platforms/telegram/telegram_file_boundary.py",
    "plugins/platforms/telegram/telegram_ingress.py",
    "plugins/platforms/telegram/telegram_document_bytes.py",
)
POLICY_MODULES = (
    "hermes_cli.friday_user_scope",
    "hermes_cli.friday_product_access",
    "hermes_cli.plugins_state",
)

def need(condition, message):
    if not condition:
        raise ValueError(message)

def digest(raw):
    return sha256(raw).hexdigest()

def encoded(data):
    return (json.dumps(data, ensure_ascii=True, sort_keys=True, allow_nan=False) + "\n").encode()

def validate_case(scenario):
    need(digest(encoded(scenario)) == SCENARIO, "Exact normalized D01 RTF phase required")
    step, = scenario["steps"]
    item = step["input"]
    need(item["sha256"] == SOURCE and item["filename"] == DISPLAY_NAME
         and item["mime_type"] == "application/rtf" and item["stat"]["size_bytes"] == 1919
         and step["observe"]["mode"] == "bounded_reply_capture"
         and step["observe"]["window_seconds"] == 180 and scenario["deadline_seconds"] == 300,
         "Exact D01 one-RTF preparation required")

def check_namespace(route, workspace):
    received = workspace / "received"
    paths = (workspace, received)
    def signatures():
        result = []
        for path in paths:
            token = route.identity(path, directory=True)
            info = path.lstat()
            need(token == (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink),
                 "D01 workspace directory changed")
            result.append((token, info.st_mtime_ns, info.st_ctime_ns))
        return tuple(result)
    before = signatures()
    need(not os.path.lexists(workspace / DISPLAY_NAME), "D01 exact source name is already present in workspace")
    registered = re.compile(r"telegram_[0-9a-f]{64}_" + re.escape(DISPLAY_NAME))
    with os.scandir(received) as listing:
        for count, entry in enumerate(listing, 1):
            need(count <= 10000, "D01 received-name inventory exceeds bound")
            need(entry.name != DISPLAY_NAME and not registered.fullmatch(entry.name),
                 "D01 exact source name is already present in received")
    need(signatures() == before, "D01 workspace name inventory changed")
    return before

def observe_current(basis, *, scenario, read_reference, load_module):
    validate_case(scenario)
    need(set(basis) == set(PINS) and all(basis[k]["sha256"] == pin for k,pin in PINS.items()),
         "D01 exact route and reader proof references required")
    core,native,pairing,route = (
        load_module(basis[k], "_d01_" + k) for k in ("core","native","pairing","route"))
    proof = route.decode(read_reference(basis["reader"]))
    need(proof["full_rows"] == 11 and proof["u2028_inside_paragraph"] == 6
         and proof["source_identity_preserved"] is True
         and proof["source_receipt_sha256"] == PINS_CORE_RECEIPT,
         "D01 exact RTF reader evidence required")
    root = core.RUNTIME
    need(root == native.HOME and sys.executable == route.NATIVE_PYTHON
         and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "D01 exact Core296 isolated interpreter required")
    uid, account = str(scenario["tester_id"]), str(scenario["peer_id"])
    profile = "telegram-bot-" + uid
    need(native.KEY == f"agent:{profile}:telegram:dm:{uid}", "D01 exact selected native lane required")
    principal = dict(id=native.SID,source="telegram",user_id=uid,chat_id=uid,chat_type="dm",
                     session_key=native.KEY,profile_name=profile,transport_profile="default")
    lane = root / "profiles" / profile
    workspace = lane / "workspace"
    source = root / "hermes-agent"
    databases = (root / "state.db", lane / "state.db")
    initial_db = tuple(route.db_outer_identity(path) for path in databases)
    initial_names = check_namespace(route, workspace)

    def receipts():
        return {path.name:digest(route.checked_read(path,limit=8*1024**2,private=False))
                for path in core.RECEIPTS}

    install = receipts()
    need(install == {path.name:pin for path,pin in core.RECEIPTS.items()},
         "D01 Core296 receipt, marker or stamp changed")
    manifest = route.decode(route.checked_read(root/"hermes-agent.source.json",limit=8*1024**2,private=False))
    need(len(manifest["layers"]) == 296, "D01 installed source layer count changed")
    roles = {}
    for name in sorted(set(ROUTE_ROLES) | set(proof["roles"])):
        pin = manifest["files"][name]
        raw = route.checked_read(source/name,limit=2*1024**2,private=False)
        need(len(raw) == pin["bytes"] and digest(raw) == pin["sha256"],
             "D01 installed capability source changed")
        if name in proof["roles"]:
            need(proof["roles"][name] == pin, "D01 tested RTF reader source changed")
        roles[name] = pin["sha256"]
    need(roles["gateway/ordinary_turn_projection.py"] == native.NATIVE_SHA,
         "D01 native projection source changed")

    def routing():
        row = route.checked_route_row(pairing, root, lane, principal, account, native)
        state = route.decode(route.checked_read(root/"gateway_state.json",private=False))
        route_state = pairing.gateway_route(state, dict(pid=state["pid"],birth_ticks=state["start_time"]), principal)
        need(not os.path.lexists(root/"maintenance.json"), "D01 maintenance in progress")
        return state,(row,route_state)

    gateway, expected_route = routing()
    venv = Path(sys.executable).parent.parent
    site = venv/"lib"/f"python{sys.version_info.major}.{sys.version_info.minor}"/"site-packages"
    need(site.resolve(strict=True) == site and site.is_dir(), "D01 exact installed Python modules required")
    previous = sys.path[:]
    try:
        sys.path[:0] = [str(source), str(site)]
        for name in POLICY_MODULES:
            module = importlib.import_module(name)
            need(Path(module.__file__) == source/(name.replace(".","/")+".py"),
                 "D01 installed policy import changed")
        observed_permissions = route.permission_snapshot(root,lane,principal,account,pairing)
        generation = native.fresh_native(gateway)
        need(observed_permissions == route.permission_snapshot(root,lane,principal,account,pairing),
             "D01 actual pairing or rights changed")
    finally:
        sys.path[:] = previous

    need(routing()[1] == expected_route and receipts() == install
         and check_namespace(route, workspace) == initial_names
         and tuple(route.db_outer_identity(path) for path in databases) == initial_db
         and generation["quiescent"], "D01 current route or installed inputs changed")
    return {
        "scenario_sha256":SCENARIO, "source_sha256":SOURCE, "preparation_sha256":PREPARATION,
        "installed":install, "roles":roles,
        "permissions":observed_permissions, "route_sha256":digest(encoded(expected_route)),
        "native_identity":generation["identity"], "native_generation":generation["generation"],
        "database_identity_sha256":digest(encoded(initial_db)), "workspace_names_admissible":True,
        "event_authority":False, "prospective_ingress":False,
    }

def check_current(binding, *, scenario, read_reference, load_module):
    need(set(binding) == {"basis","history","current_sha256"}, "D01 exact read-only binding required")
    history = json.loads(read_reference(binding["history"]))
    need(history.get("scenario_sha256") == SCENARIO and history.get("input_sha256") == SOURCE
         and history.get("matches") == [] and history.get("fresh_authority_issued") is False,
         "D01 exact collision proof unresolved")
    result = observe_current(binding["basis"],scenario=scenario,read_reference=read_reference,load_module=load_module)
    need(digest(encoded(result)) == binding["current_sha256"], "D01 actual route or permission snapshot changed")
    return True
