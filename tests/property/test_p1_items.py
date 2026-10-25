"""P1: pickup spacing and the fuel guarantee over 100 seeds."""

from __future__ import annotations

from itertools import pairwise

from hillclimb.engine.terrain import Terrain
from hillclimb.engine.world import (
    COIN_GROUP_GAP_MAX_PX,
    COIN_GROUP_GAP_MIN_PX,
    FUEL_CAN_GAP_MAX_PX,
    FUEL_CAN_GAP_MIN_PX,
    MIN_ITEM_GAP_PX,
    World,
)

SEEDS = range(100)
GENERATE_UNTIL_PX = 70_000.0


def test_p1_fuel_guarantee_and_spacing_over_100_seeds() -> None:
    for seed in SEEDS:
        terrain = Terrain(seed)
        world = World(seed, terrain)
        world.ensure_generated_until(GENERATE_UNTIL_PX)
        cans = world.fuel_cans
        assert len(cans) >= 10
        gaps = [current.x - previous.x for previous, current in pairwise(cans)]
        assert all(FUEL_CAN_GAP_MIN_PX <= gap <= FUEL_CAN_GAP_MAX_PX for gap in gaps)
        assert sum(gaps) / len(gaps) <= 4_500.0
        for previous, current in pairwise(world.coin_groups):
            assert COIN_GROUP_GAP_MIN_PX <= current.x - previous.x <= COIN_GROUP_GAP_MAX_PX
        for group in world.coin_groups:
            for can in cans:
                assert abs(group.x - can.x) >= MIN_ITEM_GAP_PX
