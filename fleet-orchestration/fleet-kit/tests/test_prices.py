"""Light/heavy shadow prices (handin/targets.py): off by default, 1.0 when the fleet covers the demand, scarce
subtypes cost more, one computation per scenario."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "handin"))

import params  # noqa: E402
import targets  # noqa: E402
from fk.model import EFFECTOR, HOSTILE, Scenario  # noqa: E402
from fleetkit.generator import generate  # noqa: E402


def l4():
    return Scenario.from_dict(generate("L4", 0))


def test_off_by_default_changes_nothing():
    s = l4()
    assert params.PRICES is False
    assert all(targets.weight(s, c) == 1.0 for c in s.contacts)


def test_scarce_light_costs_more_than_plentiful_heavy(monkeypatch):
    monkeypatch.setattr(params, "PRICES", True)
    s = l4()
    p = targets.prices(s)
    assert p["light"] > 1.0 and p["heavy"] == 1.0
    light_only = [c for c in s.contacts if c.cls == HOSTILE and set(c.needs) == {"light"}]
    heavy_only = [c for c in s.contacts if c.cls == HOSTILE and set(c.needs) == {"heavy"}]
    assert light_only and heavy_only
    assert all(targets.weight(s, c) < 1.0 for c in light_only)
    assert all(targets.weight(s, c) == 1.0 for c in heavy_only)


def test_exactly_one_when_the_fleet_covers_the_demand(monkeypatch):
    monkeypatch.setattr(params, "PRICES", True)
    d = copy.deepcopy(generate("L1", 0))
    for i, a in enumerate([a for a in d["aircraft"] if a["type"] == "effector"] * 6):
        clone = copy.deepcopy(a)
        clone["id"] = "X%d" % i
        d["aircraft"].append(clone)
    s = Scenario.from_dict(d)
    assert set(targets.prices(s).values()) == {1.0}
    assert all(targets.weight(s, c) == 1.0 for c in s.contacts)


def test_prices_are_computed_once_per_scenario(monkeypatch):
    monkeypatch.setattr(params, "PRICES", True)
    s = l4()
    assert targets.prices(s) is targets.prices(s)
    assert targets.prices(Scenario.from_dict(generate("L4", 1))) != targets.prices(s)


def test_blocked_hostiles_do_not_count_as_demand(monkeypatch):
    monkeypatch.setattr(params, "PRICES", True)
    s = l4()
    assert targets.ENABLED
    kept = {}
    for c in s.contacts:
        if c.cls == HOSTILE and not targets.skip(s, c):
            for sub, n in c.needs.items():
                kept[sub] = kept.get(sub, 0) + n
    supply = {}
    for a in s.aircraft:
        if a.type == EFFECTOR:
            supply[a.subtype] = supply.get(a.subtype, 0) + 1
    for sub, price in targets.prices(s).items():
        assert price == max(1.0, kept[sub] / supply[sub])
