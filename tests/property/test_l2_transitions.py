"""L2: planned state changes stay inside the state table until quit."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.app.main import InputSignals, planned_transition
from hillclimb.app.state import GameState, StateMachine

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

REACHABLE_STATES = (
    GameState.MENU,
    GameState.PLAY,
    GameState.PAUSED,
    GameState.GAMEOVER,
)
ALLOWED: Mapping[GameState, frozenset[GameState]] = MappingProxyType(
    {
        GameState.MENU: frozenset({GameState.PLAY}),
        GameState.PLAY: frozenset({GameState.PAUSED, GameState.GAMEOVER}),
        GameState.PAUSED: frozenset({GameState.PLAY, GameState.MENU}),
        GameState.GAMEOVER: frozenset({GameState.PLAY, GameState.MENU}),
    }
)
SIGNALS = st.builds(
    InputSignals,
    accelerate=st.floats(min_value=0.0, max_value=1.0),
    brake=st.floats(min_value=0.0, max_value=1.0),
    pressed_pause=st.booleans(),
    pressed_restart=st.booleans(),
    pressed_confirm=st.booleans(),
    pressed_back=st.booleans(),
)
STEPS = st.lists(
    st.tuples(SIGNALS, st.booleans(), st.booleans()),
    min_size=1,
    max_size=25,
)


def _machine_at(state: GameState) -> StateMachine:
    machine = StateMachine()
    machine.transition(GameState.MENU)
    if state is GameState.MENU:
        return machine
    machine.transition(GameState.PLAY)
    if state is GameState.PLAY:
        return machine
    if state is GameState.PAUSED:
        machine.transition(GameState.PAUSED)
    else:
        machine.transition(GameState.GAMEOVER)
    return machine


@settings(max_examples=50, deadline=None)
@given(start=st.sampled_from(REACHABLE_STATES), steps=STEPS)
def test_l2_transition_policy_never_skips_or_breaks_the_table(
    start: GameState, steps: Sequence[tuple[InputSignals, bool, bool]]
) -> None:
    machine = _machine_at(start)
    for signals, game_over, quit_requested in steps:
        if quit_requested:
            break
        before = machine.state
        target = planned_transition(before, signals, game_over=game_over)
        if target is not None:
            assert target in ALLOWED[before]
            assert machine.transition(target) is target
        assert machine.state in REACHABLE_STATES


def test_l2_escape_pause_wins_over_back_in_paused() -> None:
    signals = InputSignals(pressed_pause=True, pressed_back=True)
    assert planned_transition(GameState.PAUSED, signals, game_over=False) is GameState.PLAY


def test_l2_game_over_wins_over_pause_in_play() -> None:
    signals = InputSignals(pressed_pause=True)
    assert planned_transition(GameState.PLAY, signals, game_over=True) is GameState.GAMEOVER


def test_l2_restart_wins_over_back_on_game_over() -> None:
    signals = InputSignals(pressed_restart=True, pressed_back=True)
    assert planned_transition(GameState.GAMEOVER, signals, game_over=True) is GameState.PLAY


def test_l2_back_leaves_paused_for_menu() -> None:
    assert (
        planned_transition(GameState.PAUSED, InputSignals(pressed_back=True), game_over=False)
        is GameState.MENU
    )


def test_l2_confirm_enters_play_from_menu() -> None:
    assert (
        planned_transition(GameState.MENU, InputSignals(pressed_confirm=True), game_over=False)
        is GameState.PLAY
    )


def test_l2_play_idles_without_input() -> None:
    assert planned_transition(GameState.PLAY, InputSignals(), game_over=False) is None


def test_l2_boot_has_no_planned_transition() -> None:
    signals = InputSignals(pressed_confirm=True)
    assert planned_transition(GameState.BOOT, signals, game_over=False) is None
