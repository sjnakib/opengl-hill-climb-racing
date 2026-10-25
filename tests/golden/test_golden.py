"""Golden migration fixtures (SPECS §12, M1)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from hillclimb.config import Config, migrate_config
from hillclimb.savedata import SaveData, migrate_savedata

GOLDEN_DIR = Path(__file__).parent


def test_config_v0_fixture_migrates() -> None:
    raw = tomllib.loads((GOLDEN_DIR / "config_v0.toml").read_text(encoding="utf-8"))
    expected = json.loads((GOLDEN_DIR / "config_v0_expected.json").read_text(encoding="utf-8"))
    assert migrate_config(raw) == expected
    assert Config.from_mapping(expected) == Config(
        master_volume=80,
        music_volume=80,
        sfx_volume=80,
        window_width=1024,
        window_height=576,
    )


def test_save_v0_fixture_migrates() -> None:
    raw = json.loads((GOLDEN_DIR / "save_v0.json").read_text(encoding="utf-8"))
    expected = json.loads((GOLDEN_DIR / "save_v0_expected.json").read_text(encoding="utf-8"))
    assert migrate_savedata(raw) == expected
    assert SaveData.from_mapping(expected) == SaveData(best_score=1234, best_distance_m=42.5)
