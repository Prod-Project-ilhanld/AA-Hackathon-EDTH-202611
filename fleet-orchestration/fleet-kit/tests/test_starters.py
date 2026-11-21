"""Starter modules (handin/targets.py, handin/deconflict.py) are no-ops when off, and R7 skipping works when on."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "handin"))

import deconflict  # noqa: E402
import targets  # noqa: E402
from fk.model import Scenario  # noqa: E402


def test_off_by_default(scenario_dict):
    s = Scenario.from_dict(scenario_dict)
    c = s.contacts[0]
    assert targets.skip(s, c) is False and targets.weight(s, c) == 1.0
    assert deconflict.adjust(None, {}) is True


def test_r7_skip_when_enabled(scenario_dict, monkeypatch):
    monkeypatch.setattr(targets, "ENABLED", True)
    d = copy.deepcopy(scenario_dict)
    d["contacts"].append({"id": "C99", "class": "hostile", "pos": [1500, 450, 0], "points": 40,
                          "engage_needs": {"light": 1}, "window_s": [100, 800]})  # 150 m from civilian C03
    s = Scenario.from_dict(d)
    by_id = s.contact_by_id()
    assert targets.skip(s, by_id["C99"]) is True
    assert targets.skip(s, by_id["C01"]) is False  # 300 m from C03
