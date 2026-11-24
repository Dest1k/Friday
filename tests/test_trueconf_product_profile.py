"""TrueConf opt-in at the existing normal product renderer."""
import copy
import json

import pytest

from gateway.trueconf_access import CLIENT_ID_ENV, PASSWORD_ENVS, TOKEN_ENV, profile_access
from tools.configure_product import compose_product, materialize_product
from test_product_profile import inputs, template


def selected(names=PASSWORD_ENVS):
    spec = inputs()
    spec["accounts"][0]["account_id"] = "101"
    spec["accounts"].append({"platform": "trueconf", "transport_profile": "default", "account_id": "friday-product"})
    extra = {
        "server_url": "https://TRUECONF.EXAMPLE:443/",
        "account_role": "product",
        "account_id": "friday-product",
        "allowed_user_ids": ["ordinary-7"],
        "allowed_group_ids": ["group-2"],
        "allowed_dm_chat_ids": ["dm-1"],
        "tester_user_id": "friday-tester",
        "tester_chat_id": "tester-dm",
    }
    if TOKEN_ENV in names:
        extra["token_expires_at"] = 1_900_000_000
    spec["trueconf"] = {"extra": extra, "credential_names": list(names)}
    return spec


@pytest.mark.parametrize("names", [PASSWORD_ENVS, (*PASSWORD_ENVS, CLIENT_ID_ENV), (TOKEN_ENV,)])
def test_two_receivers_use_independent_credential_domains(names):
    from gateway.trueconf_access import TrueConfAccess, profile_config

    source = selected(names)
    original = copy.deepcopy(source)
    result = compose_product(source)
    cfg, contract = result["config"], result["contract"]
    assert source == original
    access = TrueConfAccess.from_config(profile_config(cfg))
    assert access.server_url == "https://trueconf.example"
    assert contract["schema"] == "friday.product-profile.v2"
    assert contract["state"] == "TEMPLATE_INCOMPLETE" and contract["ready"] is False
    assert contract["required_scoped_names"]["channels"] == {
        "telegram": ["TELEGRAM_BOT_TOKEN"], "trueconf": list(names)
    }
    assert set(contract["required_scoped_names"]["inference_web"]).isdisjoint(names)
    assert cfg["platforms"]["telegram"] == {"enabled": True}
    assert cfg["platforms"]["trueconf"]["extra"]["account_id"] == "friday-product"
    rows = cfg["plugins"]["entries"]["friday_rework"]["settings"]["product_access"]["accounts"]
    assert [v["account_id"] for v in rows] == ["101", access.scope_id]
    assert "friday-tester" not in [v["account_id"] for v in rows]
    user_template = template(result)
    assert not {"platforms", "gateway", "dashboard"} & user_template["config"].keys()
    assert set(user_template["required_secrets"]).isdisjoint(names)
    assert "file" in user_template["config"]["platform_toolsets"]["trueconf"]
    assert cfg["display"]["platforms"]["trueconf"]["show_reasoning"] is False


@pytest.mark.parametrize("edit", [
    lambda s: s["trueconf"]["extra"].update(server_url="http://outside.example"),
    lambda s: s["trueconf"]["extra"].update(server_url="https://name:secret@trueconf.example"),
    lambda s: s["trueconf"]["extra"].update(account_role="tester"),
    lambda s: s["trueconf"]["extra"].update(token="secret"),
    lambda s: s["trueconf"]["extra"].update(tls_ca_file="../cert.pem"),
    lambda s: s["trueconf"]["extra"].pop("tester_chat_id"),
    lambda s: s["trueconf"]["credential_names"].append("TELEGRAM_BOT_TOKEN"),
    lambda s: s["trueconf"]["credential_names"].append(PASSWORD_ENVS[0]),
    lambda s: s["trueconf"]["credential_names"].append({"bad": True}),
    lambda s: s["accounts"].pop(0),
    lambda s: s["accounts"].pop(),
    lambda s: s["accounts"][1].update(account_id="other-account"),
    lambda s: s["accounts"].append(dict(s["accounts"][1])),
    lambda s: s.pop("trueconf"),
    lambda s: s["trueconf"]["extra"].update(token_expires_at=1_900_000_000),
])
def test_incomplete_ambiguous_or_ambient_trueconf_does_not_render(edit):
    source = selected()
    edit(source)
    with pytest.raises(ValueError):
        compose_product(source)


@pytest.mark.parametrize("expiry", [None, True, -1, 0, "1900000000"])
def test_token_requires_explicit_epoch(expiry):
    source = selected((TOKEN_ENV,))
    source["trueconf"]["extra"]["token_expires_at"] = expiry
    with pytest.raises(ValueError, match="trueconf_token_expiry_required"):
        compose_product(source)


def test_fresh_profile_only_stages_nonsecret_admission_inputs(tmp_path):
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override

    root = tmp_path / "installation"
    root.mkdir(mode=0o700)
    home = root / "default"
    result = materialize_product(home, selected())
    assert result["ready"] is False and result["runtime_acceptance"] == "NOT_RUN"
    assert json.loads((home / "FRIDAY-PROFILE.json").read_bytes())["schema"] == "friday.product-profile.v2"
    assert not (home / ".env").exists()
    token = set_hermes_home_override(str(home))
    try:
        assert profile_access().account_id == "friday-product"
    finally:
        reset_hermes_home_override(token)
    before = (home / "config.yaml").read_bytes()
    with pytest.raises(FileExistsError):
        materialize_product(home, selected((TOKEN_ENV,)))
    assert (home / "config.yaml").read_bytes() == before


def test_extension_keeps_telegram_onboarded_users_and_routes():
    from tools.configure_product import extend_managed_trueconf

    legacy = compose_product(inputs())
    previous, contract = legacy["config"], legacy["contract"]
    settings = previous["plugins"]["entries"]["friday_rework"]["settings"]
    settings["product_access"]["accounts"][0]["runtime_profiles"].append("telegram-existing")
    settings["admin"]["profiles"].append("telegram-existing")
    settings["user_isolation"] = {"enabled": True, "bindings": [{"user_id": "synthetic-existing"}]}
    previous["gateway"]["profile_routes"] = [{"name": "synthetic-existing"}]
    initial = copy.deepcopy(legacy)

    next_cfg, next_contract = extend_managed_trueconf(previous, contract, selected()["trueconf"])
    assert legacy == initial
    assert next_contract["schema"] == "friday.product-profile.v2"
    assert next_cfg["gateway"] == previous["gateway"]
    current = next_cfg["plugins"]["entries"]["friday_rework"]["settings"]
    assert current["admin"] == settings["admin"]
    assert current["user_isolation"] == settings["user_isolation"]
    assert current["product_access"]["accounts"][0] == settings["product_access"]["accounts"][0]
    assert current["product_access"]["accounts"][1]["runtime_profiles"] == ["default"]
    assert next_cfg["providers"] == previous["providers"]
    assert next_cfg["platforms"]["telegram"] == previous["platforms"]["telegram"]

    with pytest.raises(ValueError, match="existing_telegram_profile"):
        extend_managed_trueconf(next_cfg, next_contract, selected()["trueconf"])


def test_all_trueconf_credential_names_reserved_even_for_a_password_receiver():
    from tools.configure_product import extend_managed_trueconf
    source = selected()
    source["inference"]["key_env"] = TOKEN_ENV
    with pytest.raises(ValueError, match="separate_scoped"):
        compose_product(source)
    earlier = compose_product(inputs())
    earlier["contract"]["required_scoped_names"]["inference_web"].append(TOKEN_ENV)
    with pytest.raises(ValueError, match="separate_scoped"):
        extend_managed_trueconf(earlier["config"], earlier["contract"], selected()["trueconf"])
