"""Minimal flat-color presenter for milestone C (SPECS §6, §8)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..config import Config

WINDOW_TITLE = "Hill Climb Racing"
BACKGROUND_COLOR = (118, 178, 214)


class PygamePresenter:
    """Open the configured window and present one flat-color frame."""

    __slots__ = ("_surface",)

    def __init__(self, config: Config) -> None:
        """Create the window from the validated configuration."""
        flags = pygame.FULLSCREEN if config.fullscreen else 0
        self._surface = pygame.display.set_mode(
            (config.window_width, config.window_height),
            flags,
        )
        pygame.display.set_caption(WINDOW_TITLE)

    def present(self) -> None:
        """Clear the frame to the background color and flip it."""
        self._surface.fill(BACKGROUND_COLOR)
        pygame.display.flip()
