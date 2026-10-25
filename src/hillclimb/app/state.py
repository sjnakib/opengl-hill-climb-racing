"""Game state machine for the presentation layer (SPECS §6)."""

from __future__ import annotations

import enum
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class GameState(enum.StrEnum):
    """The states a game session can occupy."""

    BOOT = "boot"
    MENU = "menu"
    PLAY = "play"
    PAUSED = "paused"
    GAMEOVER = "gameover"


class InvalidTransitionError(ValueError):
    """Raised when a state change is not allowed."""


_TRANSITIONS: Mapping[GameState, frozenset[GameState]] = MappingProxyType(
    {
        GameState.BOOT: frozenset({GameState.MENU}),
        GameState.MENU: frozenset({GameState.PLAY}),
        GameState.PLAY: frozenset({GameState.PAUSED, GameState.GAMEOVER}),
        GameState.PAUSED: frozenset({GameState.PLAY, GameState.MENU}),
        GameState.GAMEOVER: frozenset({GameState.PLAY, GameState.MENU}),
    }
)


class StateMachine:
    """Track and validate the current game state."""

    __slots__ = ("_state",)

    def __init__(self) -> None:
        """Start in BOOT."""
        self._state = GameState.BOOT

    @property
    def state(self) -> GameState:
        """Return the current state."""
        return self._state

    def transition(self, target: GameState) -> GameState:
        """Move to target when the transition table allows it."""
        if target not in _TRANSITIONS[self._state]:
            message = f"transition {self._state.value} -> {target.value} is not allowed"
            raise InvalidTransitionError(message)
        self._state = target
        return self._state

    def reset(self) -> None:
        """Return to BOOT without checking the transition table."""
        self._state = GameState.BOOT
