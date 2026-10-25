"""Tests for deterministic item generation (SPECS §10.5)."""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from hillclimb.engine.rng import RngStreams
from hillclimb.engine.terrain import Terrain
from hillclimb.engine.world import (
    COIN_GROUP_GAP_MAX_PX,
    COIN_GROUP_GAP_MIN_PX,
    COIN_RADIUS_PX,
    COIN_VALUES,
    COINS_PER_GROUP_MAX,
    COINS_PER_GROUP_MIN,
    FUEL_CAN_GAP_MAX_PX,
    FUEL_CAN_GAP_MIN_PX,
    FUEL_CAN_RADIUS_PX,
    MIN_ITEM_GAP_PX,
    World,
)


def make_world(seed: int = 21, distance: float = 30_000.0) -> World:
    terrain = Terrain(seed)
    world = World(seed, terrain)
    world.ensure_generated_until(distance)
    return world


def item_counts(world: World) -> tuple[int, int]:
    return len(world.coins), len(world.fuel_cans)


def test_world_starts_empty_and_generates_lazily() -> None:
    world = World(1, Terrain(1))
    assert item_counts(world) == (0, 0)
    world.ensure_generated_until(5.0)
    assert world.fuel_cans
    assert world.coin_groups


def test_injected_streams_match_the_default_streams() -> None:
    terrain = Terrain(2)
    first = World(2, terrain)
    second = World(2, terrain, streams=RngStreams(2))
    first.ensure_generated_until(20_000.0)
    second.ensure_generated_until(20_000.0)
    assert first.fuel_cans == second.fuel_cans
    assert first.coins == second.coins


def test_fuel_can_gaps_match_the_pinned_range() -> None:
    world = make_world()
    cans = world.fuel_cans
    assert len(cans) >= 5
    assert FUEL_CAN_GAP_MIN_PX <= cans[0].x <= FUEL_CAN_GAP_MAX_PX
    for previous, current in pairwise(cans):
        assert FUEL_CAN_GAP_MIN_PX <= current.x - previous.x <= FUEL_CAN_GAP_MAX_PX


def test_coin_group_gaps_and_sizes_match_the_table() -> None:
    world = make_world()
    groups = world.coin_groups
    assert len(groups) >= 10
    assert COIN_GROUP_GAP_MIN_PX <= groups[0].x <= COIN_GROUP_GAP_MAX_PX
    for previous, current in pairwise(groups):
        assert COIN_GROUP_GAP_MIN_PX <= current.x - previous.x <= COIN_GROUP_GAP_MAX_PX
    for group in groups:
        assert COINS_PER_GROUP_MIN <= len(group.coins) <= COINS_PER_GROUP_MAX
        for coin in group.coins:
            assert coin.value in COIN_VALUES


def test_coins_follow_the_arc_and_sit_above_the_terrain() -> None:
    terrain = Terrain(22)
    world = World(22, terrain)
    world.ensure_generated_until(20_000.0)
    for group in world.coin_groups:
        for previous, coin in pairwise(group.coins):
            dx = coin.x - previous.x
            dy = coin.y - previous.y
            arc = math.sqrt(dx * dx + dy * dy)
            assert 35.0 <= arc <= 85.0
        for coin in group.coins:
            assert coin.y - COIN_RADIUS_PX >= terrain.height_at(coin.x) - 1e-9


def test_fuel_cans_sit_above_the_terrain() -> None:
    terrain = Terrain(23)
    world = World(23, terrain)
    world.ensure_generated_until(20_000.0)
    for can in world.fuel_cans:
        assert can.y - FUEL_CAN_RADIUS_PX >= terrain.height_at(can.x) - 1e-9


def test_group_and_can_anchors_respect_the_minimum_gap() -> None:
    world = make_world(24)
    for group in world.coin_groups:
        for can in world.fuel_cans:
            assert abs(group.x - can.x) >= MIN_ITEM_GAP_PX


def test_collect_returns_the_coin_once() -> None:
    terrain = Terrain(25)
    world = World(25, terrain)
    world.ensure_generated_until(10_000.0)
    coin = world.coins[0]
    assert world.collect(coin.x, coin.y, 1.0).coin_value == coin.value
    assert world.collect(coin.x, coin.y, 1.0).coin_value == 0


def test_collect_returns_a_fuel_can_once() -> None:
    terrain = Terrain(26)
    world = World(26, terrain)
    world.ensure_generated_until(10_000.0)
    can = world.fuel_cans[0]
    assert world.collect(can.x, can.y, 1.0).fuel_cans == 1
    assert world.collect(can.x, can.y, 1.0).fuel_cans == 0


def test_collect_far_away_clears_the_buffer() -> None:
    terrain = Terrain(27)
    world = World(27, terrain)
    world.ensure_generated_until(10_000.0)
    coin = world.coins[0]
    buffer = world.collect(coin.x, coin.y, 1.0)
    assert buffer.coin_value > 0
    assert world.collect(coin.x, coin.y - 10_000.0, 1.0).coin_value == 0
    assert world.pickup_buffer is buffer


def test_collect_handles_the_last_items_and_a_missed_distance() -> None:
    terrain = Terrain(27)
    world = World(27, terrain)
    world.ensure_generated_until(10_000.0)
    last_coin = world.coins[-1]
    last_can = world.fuel_cans[-1]
    world.collect(last_coin.x, last_coin.y, 1.0)
    missed = world.collect(last_can.x, last_can.y + 100.0, 1.0)
    assert missed.fuel_cans == 0
    world.collect(last_can.x, last_can.y, 1.0)


def test_pickup_buffer_can_be_reset_directly() -> None:
    terrain = Terrain(28)
    world = World(28, terrain)
    buffer = world.pickup_buffer
    buffer.coin_value = 100
    buffer.fuel_cans = 1
    buffer.reset()
    assert buffer.coin_value == 0
    assert buffer.fuel_cans == 0


def test_coin_values_use_every_weighted_bucket() -> None:
    world = make_world(29, 200_000.0)
    values = {coin.value for coin in world.coins}
    assert values == set(COIN_VALUES)


def test_generation_rejects_nothing_for_a_large_distance() -> None:
    world = make_world(30, 120_000.0)
    cans = world.fuel_cans
    gaps = [current.x - previous.x for previous, current in pairwise(cans)]
    assert all(FUEL_CAN_GAP_MIN_PX <= gap <= FUEL_CAN_GAP_MAX_PX for gap in gaps)
    assert pytest.approx(3_500.0, abs=400.0) == sum(gaps) / len(gaps)
