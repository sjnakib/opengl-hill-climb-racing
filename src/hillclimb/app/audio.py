"""Audio bus math and the idle pygame mixer (SPECS §11)."""

from __future__ import annotations

import logging
import math

import pygame

from ..config import VOLUME_MAX, Config

_LOGGER = logging.getLogger(__name__)

MIXER_FREQUENCY = 44100
MIXER_SIZE = -16
MIXER_CHANNELS = 2
MIXER_BUFFER = 512
SFX_CHANNELS = 8


def _normalized(volume: float) -> float:
    """Return a finite 0-to-100 volume scaled to the closed 0-to-1 range."""
    if not math.isfinite(volume):
        return 0.0
    return min(max(volume, 0.0), float(VOLUME_MAX)) / float(VOLUME_MAX)


def bus_mix(master_volume: float, bus_volume: float) -> float:
    """Return the effective gain for one bus in the closed range 0 through 1."""
    return _normalized(master_volume) * _normalized(bus_volume)


def master_gain(config: Config) -> float:
    """Return the master bus gain."""
    return bus_mix(config.master_volume, VOLUME_MAX)


def music_gain(config: Config) -> float:
    """Return the music bus gain after the master stage."""
    return bus_mix(config.master_volume, config.music_volume)


def sfx_gain(config: Config) -> float:
    """Return the sfx bus gain after the master stage."""
    return bus_mix(config.master_volume, config.sfx_volume)


def pre_init_mixer() -> None:
    """Set mixer parameters before pygame.init opens the audio device."""
    pygame.mixer.pre_init(MIXER_FREQUENCY, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFER)


class AudioBackend:
    """Idle mixer that applies the configured master, music, and sfx gains."""

    __slots__ = ("_channels", "_config")

    def __init__(self, config: Config) -> None:
        """Store volumes and start with no open channels."""
        self._config = config
        self._channels: tuple[pygame.mixer.Channel, ...] = ()

    def start(self) -> None:
        """Initialize the mixer and apply the three bus gains."""
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init(
                    frequency=MIXER_FREQUENCY,
                    size=MIXER_SIZE,
                    channels=MIXER_CHANNELS,
                    buffer=MIXER_BUFFER,
                )
            except pygame.error as error:
                _LOGGER.warning("audio unavailable: %s", error)
                return
        pygame.mixer.set_num_channels(SFX_CHANNELS)
        self._channels = tuple(pygame.mixer.Channel(index) for index in range(SFX_CHANNELS))
        self.apply_volumes()

    def apply_volumes(self) -> None:
        """Apply the configured gain to the music stream and sfx channels."""
        if pygame.mixer.get_init() is None:
            return
        pygame.mixer.music.set_volume(music_gain(self._config))
        gain = sfx_gain(self._config)
        for channel in self._channels:
            channel.set_volume(gain)

    def stop(self) -> None:
        """Stop playback and close the mixer if it is open."""
        if pygame.mixer.get_init() is None:
            return
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        pygame.mixer.quit()
        self._channels = ()
