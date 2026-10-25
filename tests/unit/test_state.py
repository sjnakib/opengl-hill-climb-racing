"""Unit tests for the game state machine (SPECS §6)."""

from __future__ import annotations

import pytest

from hillclimb.app.state import GameState, InvalidTransitionError, StateMachine


def test_initial_state_is_boot() -> None:
    assert StateMachine().state is GameState.BOOT


def test_full_menu_and_run_flow() -> None:
    machine = StateMachine()
    for target in (
        GameState.MENU,
        GameState.PLAY,
        GameState.PAUSED,
        GameState.PLAY,
        GameState.GAMEOVER,
        GameState.MENU,
        GameState.PLAY,
    ):
        assert machine.transition(target) is target
        assert machine.state is target


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (GameState.BOOT, GameState.PLAY),
        (GameState.MENU, GameState.PAUSED),
        (GameState.PAUSED, GameState.GAMEOVER),
        (GameState.GAMEOVER, GameState.PAUSED),
    ],
)
def test_invalid_transitions_are_rejected(start: GameState, target: GameState) -> None:
    paths = {
        GameState.BOOT: (),
        GameState.MENU: (GameState.MENU,),
        GameState.PLAY: (GameState.MENU, GameState.PLAY),
        GameState.PAUSED: (GameState.MENU, GameState.PLAY, GameState.PAUSED),
        GameState.GAMEOVER: (GameState.MENU, GameState.PLAY, GameState.GAMEOVER),
    }
    machine = StateMachine()
    for step in paths[start]:
        machine.transition(step)
    with pytest.raises(InvalidTransitionError, match="not allowed"):
        machine.transition(target)


def test_reset_returns_to_boot_from_play() -> None:
    machine = StateMachine()
    machine.transition(GameState.MENU)
    machine.transition(GameState.PLAY)
    machine.reset()
    assert machine.state is GameState.BOOT
