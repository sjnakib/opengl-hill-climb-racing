"""Unit tests for settings persistence (SPECS §9)."""

from __future__ import annotations

import os
import tomllib
from typing import TYPE_CHECKING

import pytest

from hillclimb.config import (
    SCHEMA_VERSION,
    Config,
    ConfigStore,
    default_config_path,
    load_config,
    migrate_config,
    save_config,
    write_text_atomic,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_defaults_match_the_contract() -> None:
    config = Config()
    assert config.schema_version == SCHEMA_VERSION
    assert (config.master_volume, config.music_volume, config.sfx_volume) == (100, 100, 100)
    assert (config.window_width, config.window_height) == (1280, 720)
    assert config.fullscreen is False


def test_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    store = ConfigStore(path)
    config = Config(
        master_volume=25,
        music_volume=0,
        sfx_volume=75,
        window_width=1024,
        window_height=576,
        fullscreen=True,
    )
    store.save(config)
    assert store.path == path
    assert store.load() == config
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == SCHEMA_VERSION


def test_missing_file_returns_defaults_without_creating_it(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    assert ConfigStore(path).load() == Config()
    assert not path.exists()


def test_module_helpers_use_the_given_path(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    save_config(Config(master_volume=12), path)
    assert load_config(path).master_volume == 12


def test_unknown_fields_and_newer_schema_are_tolerated(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        'schema_version = 99\nmaster_volume = 10\nfuture_setting = "kept in spirit"\n',
        encoding="utf-8",
    )
    config = ConfigStore(path).load()
    assert config.master_volume == 10
    assert config.schema_version == SCHEMA_VERSION


def test_bad_values_are_clamped_or_defaulted() -> None:
    config = Config.from_mapping(
        {
            "master_volume": 500,
            "music_volume": -3,
            "sfx_volume": "loud",
            "window_width": 1,
            "window_height": 99_999,
            "fullscreen": "yes",
        }
    )
    assert config.master_volume == 100
    assert config.music_volume == 0
    assert config.sfx_volume == 100
    assert config.window_width == 320
    assert config.window_height == 4320
    assert config.fullscreen is False


def test_out_of_range_volumes_are_rejected() -> None:
    with pytest.raises(ValueError, match="master_volume"):
        Config(master_volume=101)


def test_out_of_range_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="window_width"):
        Config(window_width=1)


def test_wrong_schema_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        Config(schema_version=2)


def test_wrong_fullscreen_type_is_rejected() -> None:
    with pytest.raises(TypeError, match="fullscreen"):
        Config(fullscreen=1)  # type: ignore[arg-type]


def test_corrupt_toml_is_backed_up_and_replaced(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    original = "this is not toml ="
    path.write_text(original, encoding="utf-8")
    assert ConfigStore(path).load() == Config()
    assert tomllib.loads(path.read_text(encoding="utf-8"))["schema_version"] == SCHEMA_VERSION
    backups = list(tmp_path.glob("config.toml.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original


def test_invalid_utf8_is_backed_up_and_replaced(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_bytes(b"\xff\xfe\x00")
    assert ConfigStore(path).load() == Config()
    assert path.exists()
    assert len(list(tmp_path.glob("config.toml.corrupt-*.bak"))) == 1


def test_atomic_write_leaves_no_temp_files(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    write_text_atomic(path, "schema_version = 1\n")
    assert path.read_text(encoding="utf-8") == "schema_version = 1\n"
    assert list(tmp_path.glob(".config.toml.*.tmp")) == []


def test_atomic_write_failure_preserves_the_old_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.toml"
    path.write_text("old", encoding="utf-8")

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        message = "disk full"
        raise OSError(message)

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="disk full"):
        write_text_atomic(path, "new")
    assert path.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".config.toml.*.tmp")) == []


def test_default_config_path_uses_the_app_directory() -> None:
    path = default_config_path()
    assert path.name == "config.toml"
    assert path.parent.name == "hillclimb"


def test_legacy_mapping_migrates_in_place() -> None:
    raw: dict[str, object] = {
        "schema_version": 0,
        "volume": 80,
        "width": 1024,
        "height": 576,
        "theme": "classic",
    }
    migrated = migrate_config(raw)
    assert raw["volume"] == 80
    assert migrated["schema_version"] == SCHEMA_VERSION
    assert migrated["master_volume"] == 80
    assert migrated["window_width"] == 1024
    assert migrated["theme"] == "classic"
