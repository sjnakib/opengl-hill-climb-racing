"""Deterministic pickups and fuel cans on the terrain (SPECS §10.5)."""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .rng import RngStreams

if TYPE_CHECKING:
    from collections.abc import Callable

    from .terrain import Terrain

COIN_VALUES = (50, 100, 200, 500, 1000, 5000)
COIN_WEIGHTS = (0.40, 0.25, 0.15, 0.12, 0.06, 0.02)
_COIN_CUMULATIVE = (0.40, 0.65, 0.80, 0.92, 0.98, 1.0)
COIN_RADIUS_PX = 10.0
FUEL_CAN_RADIUS_PX = 16.0

COIN_GROUP_GAP_MIN_PX = 700.0
COIN_GROUP_GAP_MAX_PX = 1_100.0
COINS_PER_GROUP_MIN = 2
COINS_PER_GROUP_MAX = 6
COIN_SPACING_MIN_PX = 40.0
COIN_SPACING_MAX_PX = 80.0

FUEL_CAN_GAP_MIN_PX = 2_000.0
FUEL_CAN_GAP_MAX_PX = 5_000.0
MIN_ITEM_GAP_PX = 250.0

PICKUP_RADIUS_PX = 42.0
_LOOKAHEAD_PX = 6_000.0
_ITEM_HEIGHT_PX = 0.5


@dataclass(frozen=True, slots=True)
class Coin:
    """One collectible coin."""

    coin_id: int
    x: float
    y: float
    value: int


@dataclass(frozen=True, slots=True)
class FuelCan:
    """One fuel can that refills the tank."""

    can_id: int
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class CoinGroup:
    """A contiguous arc of coins with one anchor position."""

    group_id: int
    x: float
    coins: tuple[Coin, ...]


class PickupBuffer:
    """Reusable result buffer for one collection query."""

    __slots__ = ("coin_value", "fuel_cans")

    def __init__(self) -> None:
        """Start with an empty result."""
        self.coin_value = 0
        self.fuel_cans = 0

    def reset(self) -> None:
        """Clear the last query without allocating."""
        self.coin_value = 0
        self.fuel_cans = 0


class World:
    """Lazily generated coins and fuel cans for one run."""

    __slots__ = (
        "_buffer",
        "_can_collected",
        "_can_xs",
        "_cans",
        "_coin_collected",
        "_coin_xs",
        "_coins",
        "_groups",
        "_last_can_x",
        "_next_can_x",
        "_next_coin_id",
        "_next_group_id",
        "_next_group_x",
        "_stream",
        "_terrain",
    )

    def __init__(
        self,
        master_seed: int,
        terrain: Terrain,
        *,
        streams: RngStreams | None = None,
    ) -> None:
        """Create empty pickup lists and seed the items stream."""
        registry = RngStreams(master_seed) if streams is None else streams
        self._stream = registry.stream("items")
        self._terrain = terrain
        self._coins: list[Coin] = []
        self._coin_xs: list[float] = []
        self._coin_collected: list[bool] = []
        self._cans: list[FuelCan] = []
        self._can_xs: list[float] = []
        self._can_collected: list[bool] = []
        self._groups: list[CoinGroup] = []
        self._next_coin_id = 0
        self._next_group_id = 0
        self._last_can_x = 0.0
        self._next_can_x = self._stream.uniform(FUEL_CAN_GAP_MIN_PX, FUEL_CAN_GAP_MAX_PX)
        self._next_group_x = self._stream.uniform(COIN_GROUP_GAP_MIN_PX, COIN_GROUP_GAP_MAX_PX)
        self._buffer = PickupBuffer()

    @property
    def coins(self) -> tuple[Coin, ...]:
        """Return every generated coin."""
        return tuple(self._coins)

    @property
    def fuel_cans(self) -> tuple[FuelCan, ...]:
        """Return every generated fuel can."""
        return tuple(self._cans)

    @property
    def coin_groups(self) -> tuple[CoinGroup, ...]:
        """Return every generated coin group."""
        return tuple(self._groups)

    @property
    def pickup_buffer(self) -> PickupBuffer:
        """Return the reusable collection buffer."""
        return self._buffer

    def ensure_generated_until(self, x_px: float) -> None:
        """Generate every item up to a horizontal position."""
        target = x_px + _LOOKAHEAD_PX
        # Groups are generated first and one horizon ahead, so a late group
        # can never land on a can that was already placed.
        self._ensure_groups_until(target)
        self._ensure_cans_until(target)

    def collect(
        self, x_px: float, y_px: float, radius_px: float = PICKUP_RADIUS_PX
    ) -> PickupBuffer:
        """Collect nearby items into the reusable buffer and return it."""
        self.ensure_generated_until(x_px + radius_px)
        self._buffer.reset()
        radius_squared = radius_px * radius_px
        first = bisect_left(self._coin_xs, x_px - radius_px)
        index = first
        while index < len(self._coins):
            coin = self._coins[index]
            if coin.x > x_px + radius_px:
                break
            if not self._coin_collected[index]:
                dx = coin.x - x_px
                dy = coin.y - y_px
                if dx * dx + dy * dy <= radius_squared:
                    self._coin_collected[index] = True
                    self._buffer.coin_value += coin.value
            index += 1
        first = bisect_left(self._can_xs, x_px - radius_px)
        index = first
        while index < len(self._cans):
            can = self._cans[index]
            if can.x > x_px + radius_px:
                break
            if not self._can_collected[index]:
                dx = can.x - x_px
                dy = can.y - y_px
                if dx * dx + dy * dy <= radius_squared:
                    self._can_collected[index] = True
                    self._buffer.fuel_cans += 1
            index += 1
        return self._buffer

    def _ensure_cans_until(self, target_x: float) -> None:
        while self._next_can_x <= target_x:
            candidate = self._next_can_x - self._last_can_x
            if not self._can_gap_is_free(candidate):
                self._next_can_x = self._last_can_x + self._draw_gap(
                    FUEL_CAN_GAP_MIN_PX, FUEL_CAN_GAP_MAX_PX, self._can_gap_is_free
                )
                continue
            self._add_can(self._next_can_x)
            self._last_can_x = self._next_can_x
            self._next_can_x = self._last_can_x + self._draw_gap(
                FUEL_CAN_GAP_MIN_PX, FUEL_CAN_GAP_MAX_PX, self._can_gap_is_free
            )

    def _ensure_groups_until(self, target_x: float) -> None:
        while self._next_group_x <= target_x:
            self._add_group(self._next_group_x)
            self._next_group_x += self._stream.uniform(COIN_GROUP_GAP_MIN_PX, COIN_GROUP_GAP_MAX_PX)

    def _draw_gap(self, minimum: float, maximum: float, is_free: Callable[[float], bool]) -> float:
        while True:
            gap = self._stream.uniform(minimum, maximum)
            if is_free(gap):
                return gap

    def _can_gap_is_free(self, candidate: float) -> bool:
        x_px = self._last_can_x + candidate
        return all(abs(x_px - group.x) >= MIN_ITEM_GAP_PX for group in self._groups)

    def _add_can(self, x_px: float) -> None:
        self._cans.append(
            FuelCan(
                can_id=len(self._cans),
                x=x_px,
                y=self._terrain.height_at(x_px) + FUEL_CAN_RADIUS_PX + _ITEM_HEIGHT_PX,
            )
        )
        self._can_xs.append(x_px)
        self._can_collected.append(False)

    def _add_group(self, anchor_x: float) -> None:
        count = self._stream.randint(COINS_PER_GROUP_MIN, COINS_PER_GROUP_MAX)
        coins: list[Coin] = []
        x_px = anchor_x
        for index in range(count):
            if index:
                spacing = self._stream.uniform(COIN_SPACING_MIN_PX, COIN_SPACING_MAX_PX)
                grade = self._terrain.grade_at(x_px)
                x_px += spacing / math.sqrt(1.0 + grade * grade)
            value = self._draw_coin_value()
            coin = Coin(
                coin_id=self._next_coin_id,
                x=x_px,
                y=self._terrain.height_at(x_px) + COIN_RADIUS_PX + _ITEM_HEIGHT_PX,
                value=value,
            )
            self._next_coin_id += 1
            coins.append(coin)
        group = CoinGroup(group_id=self._next_group_id, x=anchor_x, coins=tuple(coins))
        self._next_group_id += 1
        self._groups.append(group)
        for coin in coins:
            self._coins.append(coin)
            self._coin_xs.append(coin.x)
            self._coin_collected.append(False)

    def _draw_coin_value(self) -> int:
        roll = self._stream.random()
        index = bisect_right(_COIN_CUMULATIVE, roll)
        return COIN_VALUES[min(index, len(COIN_VALUES) - 1)]
