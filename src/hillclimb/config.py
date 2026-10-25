"""Settings storage with schema versioning and atomic writes (SPECS §9)."""

from __future__ import annotations

import logging
import math
import os
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import tomli_w
from platformdirs import user_config_dir

if TYPE_CHECKING:
    from collections.abc import Mapping

_LOGGER = logging.getLogger(__name__)

APP_DIR_NAME = "hillclimb"
CONFIG_FILENAME = "config.toml"
SCHEMA_VERSION = 1

VOLUME_MIN = 0
VOLUME_MAX = 100
WINDOW_WIDTH_MIN = 320
WINDOW_WIDTH_MAX = 7680
WINDOW_HEIGHT_MIN = 240
WINDOW_HEIGHT_MAX = 4320

DEFAULT_MASTER_VOLUME = 100
DEFAULT_MUSIC_VOLUME = 100
DEFAULT_SFX_VOLUME = 100
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
DEFAULT_FULLSCREEN = False


def clamp_int(value: object, default: int, minimum: int, maximum: int) -> int:
    """Return value clamped to the range, or default when it is not an int."""
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return min(max(value, minimum), maximum)


def clamp_non_negative_float(value: object, default: float) -> float:
    """Return a finite, non-negative float, or default when value is unusable."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    try:
        numeric = float(value)
    except OverflowError, ValueError:
        return default
    if not math.isfinite(numeric) or numeric < 0.0:
        return default
    return numeric


def as_bool(value: object, *, default: bool) -> bool:
    """Return value when it is a bool, else default."""
    return value if isinstance(value, bool) else default


def _is_bool(value: object) -> bool:
    return isinstance(value, bool)


def raw_schema_version(raw: Mapping[str, object]) -> int:
    """Return the mapping schema version, treating unknown values as version 0."""
    value = raw.get("schema_version")
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def migrate_config(raw: Mapping[str, object]) -> dict[str, object]:
    """Migrate a raw settings mapping to the current schema, keeping unknown keys."""
    migrated = dict(raw)
    if raw_schema_version(raw) >= SCHEMA_VERSION:
        return migrated
    volume = migrated.pop("volume", None)
    if volume is not None:
        migrated.setdefault("master_volume", volume)
        migrated.setdefault("music_volume", volume)
        migrated.setdefault("sfx_volume", volume)
    width = migrated.pop("width", None)
    if width is not None:
        migrated.setdefault("window_width", width)
    height = migrated.pop("height", None)
    if height is not None:
        migrated.setdefault("window_height", height)
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated


@dataclass(frozen=True, slots=True)
class Config:
    """Validated settings for schema version 1."""

    schema_version: int = SCHEMA_VERSION
    master_volume: int = DEFAULT_MASTER_VOLUME
    music_volume: int = DEFAULT_MUSIC_VOLUME
    sfx_volume: int = DEFAULT_SFX_VOLUME
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    fullscreen: bool = DEFAULT_FULLSCREEN

    def __post_init__(self) -> None:
        """Reject values the game cannot run with."""
        if isinstance(self.schema_version, bool) or not isinstance(self.schema_version, int):
            message = f"schema_version must be an int, got {type(self.schema_version).__name__}"
            raise TypeError(message)
        if self.schema_version != SCHEMA_VERSION:
            message = f"schema_version must be {SCHEMA_VERSION}, got {self.schema_version!r}"
            raise ValueError(message)
        ranges = (
            ("master_volume", self.master_volume, VOLUME_MIN, VOLUME_MAX),
            ("music_volume", self.music_volume, VOLUME_MIN, VOLUME_MAX),
            ("sfx_volume", self.sfx_volume, VOLUME_MIN, VOLUME_MAX),
            ("window_width", self.window_width, WINDOW_WIDTH_MIN, WINDOW_WIDTH_MAX),
            ("window_height", self.window_height, WINDOW_HEIGHT_MIN, WINDOW_HEIGHT_MAX),
        )
        for name, value, minimum, maximum in ranges:
            if isinstance(value, bool) or not isinstance(value, int):
                message = f"{name} must be an int, got {type(value).__name__}"
                raise TypeError(message)
            if not minimum <= value <= maximum:
                message = f"{name} must be in [{minimum}, {maximum}], got {value}"
                raise ValueError(message)
        if not _is_bool(self.fullscreen):
            message = f"fullscreen must be a bool, got {type(self.fullscreen).__name__}"
            raise TypeError(message)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> Config:
        """Build settings from a mapping, tolerating unknown or bad fields."""
        return cls(
            master_volume=clamp_int(
                raw.get("master_volume"), DEFAULT_MASTER_VOLUME, VOLUME_MIN, VOLUME_MAX
            ),
            music_volume=clamp_int(
                raw.get("music_volume"), DEFAULT_MUSIC_VOLUME, VOLUME_MIN, VOLUME_MAX
            ),
            sfx_volume=clamp_int(raw.get("sfx_volume"), DEFAULT_SFX_VOLUME, VOLUME_MIN, VOLUME_MAX),
            window_width=clamp_int(
                raw.get("window_width"),
                DEFAULT_WINDOW_WIDTH,
                WINDOW_WIDTH_MIN,
                WINDOW_WIDTH_MAX,
            ),
            window_height=clamp_int(
                raw.get("window_height"),
                DEFAULT_WINDOW_HEIGHT,
                WINDOW_HEIGHT_MIN,
                WINDOW_HEIGHT_MAX,
            ),
            fullscreen=as_bool(raw.get("fullscreen"), default=DEFAULT_FULLSCREEN),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a TOML-ready mapping with schema_version first."""
        return asdict(self)


def default_config_path() -> Path:
    """Return the platform settings path for config.toml."""
    # Roaming config keeps SPECS §9's %APPDATA% path on Windows; Linux and macOS ignore it.
    directory = user_config_dir(APP_DIR_NAME, appauthor=False, roaming=True)
    return Path(directory) / CONFIG_FILENAME


def write_text_atomic(path: Path, text: str) -> None:
    """Replace path atomically, leaving either the old file or the new one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    try:
        # Path.replace has os.replace semantics, so the target swaps atomically.
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


class ConfigStore:
    """Read and write the settings TOML under a platform path."""

    def __init__(self, path: Path | None = None) -> None:
        """Use path when given, else the platform settings path."""
        self._path = path if path is not None else default_config_path()

    @property
    def path(self) -> Path:
        """Return the file this store reads and writes."""
        return self._path

    def load(self) -> Config:
        """Load settings, returning defaults when the file is missing."""
        if not self._path.exists():
            return Config()
        try:
            raw = tomllib.loads(self._path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            return self._recover_corrupt(error)
        return Config.from_mapping(migrate_config(raw))

    def save(self, config: Config) -> None:
        """Write settings atomically."""
        write_text_atomic(self._path, tomli_w.dumps(config.to_dict()))

    def _recover_corrupt(self, error: Exception) -> Config:
        backup = backup_corrupt_file(self._path)
        _LOGGER.warning("moved corrupt settings %s to %s: %s", self._path, backup, error)
        defaults = Config()
        self.save(defaults)
        return defaults


def _corrupt_backup_path(path: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return path.with_name(f"{path.name}.corrupt-{timestamp}.bak")


def backup_corrupt_file(path: Path) -> Path:
    """Move a corrupt file to its timestamped backup path and return that path."""
    backup = _corrupt_backup_path(path)
    path.replace(backup)
    return backup


def load_config(path: Path | None = None) -> Config:
    """Load settings from path, or from the platform settings path."""
    return ConfigStore(path).load()


def save_config(config: Config, path: Path | None = None) -> None:
    """Write settings to path, or to the platform settings path."""
    ConfigStore(path).save(config)
