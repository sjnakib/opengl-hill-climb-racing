"""Unit tests for best-score persistence (SPECS §9)."""

from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING

import pytest

from hillclimb.savedata import (
    BEST_SCORE_MAX,
    DEFAULT_BEST_DISTANCE_M,
    DEFAULT_BEST_SCORE,
    SCHEMA_VERSION,
    SaveData,
    SaveStore,
    default_save_path,
    load_save,
    migrate_savedata,
    save_save,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_defaults_match_the_contract() -> None:
    data = SaveData()
    assert data.schema_version == SCHEMA_VERSION
    assert data.best_score == DEFAULT_BEST_SCORE
    assert data.best_distance_m == DEFAULT_BEST_DISTANCE_M


def test_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    store = SaveStore(path)
    data = SaveData(best_score=1234, best_distance_m=42.5)
    store.save(data)
    assert store.path == path
    assert store.load() == data
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION


def test_missing_file_returns_defaults_without_creating_it(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    assert SaveStore(path).load() == SaveData()
    assert not path.exists()


def test_module_helpers_use_the_given_path(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    save_save(SaveData(best_score=99), path)
    assert load_save(path).best_score == 99


def test_unknown_fields_and_newer_schema_are_tolerated(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text(
        json.dumps({"schema_version": 7, "best_score": 55, "future": True}),
        encoding="utf-8",
    )
    data = SaveStore(path).load()
    assert data.best_score == 55
    assert data.schema_version == SCHEMA_VERSION


def test_bad_values_are_clamped_or_defaulted() -> None:
    data = SaveData.from_mapping(
        {"best_score": -4, "best_distance_m": "far"},
    )
    assert data.best_score == 0
    assert data.best_distance_m == 0.0
    assert SaveData.from_mapping({"best_score": 10**30}).best_score == BEST_SCORE_MAX
    assert SaveData.from_mapping({"best_distance_m": -2}).best_distance_m == 0.0
    assert SaveData.from_mapping({"best_distance_m": math.inf}).best_distance_m == 0.0


def test_negative_score_is_rejected_by_the_dataclass() -> None:
    with pytest.raises(ValueError, match="best_score"):
        SaveData(best_score=-1)


def test_non_finite_distance_is_rejected_by_the_dataclass() -> None:
    with pytest.raises(ValueError, match="best_distance_m"):
        SaveData(best_distance_m=math.nan)


def test_wrong_schema_version_is_rejected_by_the_dataclass() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        SaveData(schema_version=2)


def test_corrupt_json_is_backed_up_and_replaced(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    original = "{not json"
    path.write_text(original, encoding="utf-8")
    assert SaveStore(path).load() == SaveData()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == SCHEMA_VERSION
    backups = list(tmp_path.glob("save.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original


def test_non_object_json_is_backed_up_and_replaced(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert SaveStore(path).load() == SaveData()
    assert len(list(tmp_path.glob("save.json.corrupt-*.bak"))) == 1


def test_invalid_utf8_is_backed_up_and_replaced(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_bytes(b"\xff\xfe\x00")
    assert SaveStore(path).load() == SaveData()
    assert path.exists()
    assert len(list(tmp_path.glob("save.json.corrupt-*.bak"))) == 1


def test_default_save_path_uses_the_app_directory() -> None:
    path = default_save_path()
    assert path.name == "save.json"
    assert path.parent.name == "hillclimb"


def test_legacy_mapping_migrates_in_place() -> None:
    raw: dict[str, object] = {"schema_version": 0, "best": 1234, "distance": 42.5}
    migrated = migrate_savedata(raw)
    assert raw["best"] == 1234
    assert migrated["schema_version"] == SCHEMA_VERSION
    assert migrated["best_score"] == 1234
    assert migrated["best_distance_m"] == 42.5
