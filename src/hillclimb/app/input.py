"""Keyboard and gamepad input mapping (SPECS §10.6)."""

from __future__ import annotations

import pygame
from pygame._sdl2 import controller

from .main import InputSignals

ACCELERATE_KEYS = (pygame.K_RIGHT, pygame.K_d)
BRAKE_KEYS = (pygame.K_LEFT, pygame.K_a)
PAUSE_KEYS = (pygame.K_ESCAPE,)
RESTART_KEYS = (pygame.K_r,)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
BACK_KEYS = (pygame.K_ESCAPE,)

PAD_ACCELERATE = pygame.CONTROLLER_BUTTON_A
PAD_BRAKE = pygame.CONTROLLER_BUTTON_X
PAD_PAUSE = pygame.CONTROLLER_BUTTON_START
PAD_RESTART = pygame.CONTROLLER_BUTTON_Y
PAD_CONFIRM = pygame.CONTROLLER_BUTTON_A
PAD_BACK = pygame.CONTROLLER_BUTTON_B


class PygameInput:
    """Keyboard and gamepad input port for pygame-ce."""

    __slots__ = ("_controllers", "_quit_requested")

    def __init__(self) -> None:
        """Open the controller API and attach pads already plugged in."""
        self._controllers: list[controller.Controller] = []
        self._quit_requested = False
        try:
            controller.init()
        except pygame.error:
            return
        for index in range(controller.get_count()):
            self._open_controller(index)

    def sample(self) -> InputSignals:
        """Return held levels and this frame's edge flags."""
        pause, restart, confirm, back = self._read_edges()
        accelerate, brake = self._read_levels()
        return InputSignals(
            accelerate=accelerate,
            brake=brake,
            pressed_pause=pause,
            pressed_restart=restart,
            pressed_confirm=confirm,
            pressed_back=back,
        )

    def quit_requested(self) -> bool:
        """Return whether a pygame QUIT event has arrived."""
        return self._quit_requested

    def close(self) -> None:
        """Release the controller subsystem."""
        try:
            controller.quit()
        except pygame.error:
            return

    def _open_controller(self, index: int) -> None:
        try:
            pad = controller.Controller(index)
        except pygame.error:
            return
        self._controllers.append(pad)

    def _read_edges(self) -> tuple[bool, bool, bool, bool]:
        pause = False
        restart = False
        confirm = False
        back = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit_requested = True
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                key = event.key
                pause = pause or key in PAUSE_KEYS
                restart = restart or key in RESTART_KEYS
                confirm = confirm or key in CONFIRM_KEYS
                back = back or key in BACK_KEYS
            elif event.type == pygame.CONTROLLERBUTTONDOWN:
                button = event.button
                pause = pause or button == PAD_PAUSE
                restart = restart or button == PAD_RESTART
                confirm = confirm or button == PAD_CONFIRM
                back = back or button == PAD_BACK
        return pause, restart, confirm, back

    def _read_levels(self) -> tuple[float, float]:
        keys = pygame.key.get_pressed()
        accelerate = 1.0 if keys[ACCELERATE_KEYS[0]] or keys[ACCELERATE_KEYS[1]] else 0.0
        brake = 1.0 if keys[BRAKE_KEYS[0]] or keys[BRAKE_KEYS[1]] else 0.0
        for pad in self._controllers:
            try:
                if pad.get_button(PAD_ACCELERATE):
                    accelerate = 1.0
                if pad.get_button(PAD_BRAKE):
                    brake = 1.0
            except pygame.error:
                continue
        return accelerate, brake
