"""M1: config and save round-trip and migration properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hillclimb.config import SCHEMA_VERSION, Config, ConfigStore, migrate_config
from hillclimb.savedata import SaveData, SaveStore, migrate_savedata

if TYPE_CHECKING:
    from pathlib import Path

CONFIG_STRATEGY = st.builds(
    Config,
    master_volume=st.integers(min_value=0, max_value=100),
    music_volume=st.integers(min_value=0, max_value=100),
    sfx_volume=st.integers(min_value=0, max_value=100),
    window_width=st.integers(min_value=320, max_value=7680),
    window_height=st.integers(min_value=240, max_value=4320),
    fullscreen=st.booleans(),
)
SAVE_STRATEGY = st.builds(
    SaveData,
    best_score=st.integers(min_value=0, max_value=10**12),
    best_distance_m=st.floats(
        min_value=0.0,
        max_value=1e9,
        allow_nan=False,
        allow_infinity=False,
    ),
)
SCALAR_STRATEGY = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10**9), max_value=10**9),
    st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
    st.text(max_size=20),
)
RAW_STRATEGY = st.dictionaries(st.text(max_size=20), SCALAR_STRATEGY, max_size=8)


@given(config=CONFIG_STRATEGY)
def test_config_mapping_round_trip(config: Config) -> None:
    assert Config.from_mapping(config.to_dict()) == config


@given(data=SAVE_STRATEGY)
def test_save_mapping_round_trip(data: SaveData) -> None:
    assert SaveData.from_mapping(data.to_dict()) == data


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(config=CONFIG_STRATEGY)
def test_config_store_round_trip(config: Config, tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.save(config)
    assert store.load() == config


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(data=SAVE_STRATEGY)
def test_save_store_round_trip(data: SaveData, tmp_path: Path) -> None:
    store = SaveStore(tmp_path / "save.json")
    store.save(data)
    assert store.load() == data


@settings(max_examples=60)
@given(raw=RAW_STRATEGY)
def test_config_migration_is_idempotent_and_tolerant(raw: dict[str, object]) -> None:
    migrated = migrate_config(raw)
    assert migrate_config(migrated) == migrated
    assert Config.from_mapping(migrated).schema_version == SCHEMA_VERSION


@settings(max_examples=60)
@given(raw=RAW_STRATEGY)
def test_save_migration_is_idempotent_and_tolerant(raw: dict[str, object]) -> None:
    migrated = migrate_savedata(raw)
    assert migrate_savedata(migrated) == migrated
    assert SaveData.from_mapping(migrated).schema_version == SCHEMA_VERSION
