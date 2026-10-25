"""Best-score persistence with schema versioning and atomic writes (SPECS §9)."""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from platformdirs import user_data_dir

from .config import (
    APP_DIR_NAME,
    backup_corrupt_file,
    clamp_int,
    clamp_non_negative_float,
    raw_schema_version,
    write_text_atomic,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

_LOGGER = logging.getLogger(__name__)

SAVE_FILENAME = "save.json"
SCHEMA_VERSION = 1

DEFAULT_BEST_SCORE = 0
BEST_SCORE_MIN = 0
BEST_SCORE_MAX = 2**53 - 1
DEFAULT_BEST_DISTANCE_M = 0.0


def migrate_savedata(raw: Mapping[str, object]) -> dict[str, object]:
    """Migrate a raw save mapping to the current schema, keeping unknown keys."""
    migrated = dict(raw)
    if raw_schema_version(raw) >= SCHEMA_VERSION:
        return migrated
    best = migrated.pop("best", None)
    if best is not None:
        migrated.setdefault("best_score", best)
    distance = migrated.pop("distance", None)
    if distance is not None:
        migrated.setdefault("best_distance_m", distance)
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated


@dataclass(frozen=True, slots=True)
class SaveData:
    """Validated best-score record for schema version 1."""

    schema_version: int = SCHEMA_VERSION
    best_score: int = DEFAULT_BEST_SCORE
    best_distance_m: float = DEFAULT_BEST_DISTANCE_M

    def __post_init__(self) -> None:
        """Reject values the game cannot store."""
        if isinstance(self.schema_version, bool) or not isinstance(self.schema_version, int):
            message = f"schema_version must be an int, got {type(self.schema_version).__name__}"
            raise TypeError(message)
        if self.schema_version != SCHEMA_VERSION:
            message = f"schema_version must be {SCHEMA_VERSION}, got {self.schema_version!r}"
            raise ValueError(message)
        if isinstance(self.best_score, bool) or not isinstance(self.best_score, int):
            message = f"best_score must be an int, got {type(self.best_score).__name__}"
            raise TypeError(message)
        if not BEST_SCORE_MIN <= self.best_score <= BEST_SCORE_MAX:
            message = f"best_score must be in [{BEST_SCORE_MIN}, {BEST_SCORE_MAX}]"
            raise ValueError(message)
        if isinstance(self.best_distance_m, bool) or not isinstance(
            self.best_distance_m, (int, float)
        ):
            message = "best_distance_m must be numeric"
            raise TypeError(message)
        distance = float(self.best_distance_m)
        if not math.isfinite(distance) or distance < 0.0:
            message = f"best_distance_m must be finite and non-negative, got {distance!r}"
            raise ValueError(message)
        object.__setattr__(self, "best_distance_m", distance)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> SaveData:
        """Build a save record from a mapping, tolerating unknown or bad fields."""
        return cls(
            best_score=clamp_int(
                raw.get("best_score"), DEFAULT_BEST_SCORE, BEST_SCORE_MIN, BEST_SCORE_MAX
            ),
            best_distance_m=clamp_non_negative_float(
                raw.get("best_distance_m"), DEFAULT_BEST_DISTANCE_M
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready mapping with schema_version first."""
        return asdict(self)


def default_save_path() -> Path:
    """Return the platform data path for save.json."""
    directory = user_data_dir(APP_DIR_NAME, appauthor=False, roaming=False)
    return Path(directory) / SAVE_FILENAME


class SaveStore:
    """Read and write the best-score JSON under a platform path."""

    def __init__(self, path: Path | None = None) -> None:
        """Use path when given, else the platform save path."""
        self._path = path if path is not None else default_save_path()

    @property
    def path(self) -> Path:
        """Return the file this store reads and writes."""
        return self._path

    def load(self) -> SaveData:
        """Load the record, returning defaults when the file is missing."""
        if not self._path.exists():
            return SaveData()
        try:
            payload: object = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            return self._recover_corrupt(error)
        if not isinstance(payload, dict):
            return self._recover_corrupt(ValueError("save file top level must be a JSON object"))
        return SaveData.from_mapping(migrate_savedata(payload))

    def save(self, data: SaveData) -> None:
        """Write the record atomically."""
        text = json.dumps(data.to_dict(), indent=2, sort_keys=True, allow_nan=False)
        write_text_atomic(self._path, f"{text}\n")

    def _recover_corrupt(self, error: Exception) -> SaveData:
        backup = backup_corrupt_file(self._path)
        _LOGGER.warning("moved corrupt save %s to %s: %s", self._path, backup, error)
        defaults = SaveData()
        self.save(defaults)
        return defaults


def load_save(path: Path | None = None) -> SaveData:
    """Load the best-score record from path, or from the platform save path."""
    return SaveStore(path).load()


def save_save(data: SaveData, path: Path | None = None) -> None:
    """Write the best-score record to path, or to the platform save path."""
    SaveStore(path).save(data)
