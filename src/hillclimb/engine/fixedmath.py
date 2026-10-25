"""Deterministic IEEE-only trigonometry for the engine (SPECS §10.2).

The engine may not call libm transcendentals because their last bits differ
across platforms. This module reduces an angle with ``% TAU`` and evaluates a
fixed polynomial with ordinary arithmetic only.
"""

from __future__ import annotations

import math

TAU = 6.283185307179586
PI = 3.141592653589793
HALF_PI = 1.5707963267948966

# True 2*pi minus the double nearest to it. The correction below removes the
# drift that a long run would otherwise accumulate from the rounded TAU.
_TAU_TAIL = 2.4492935982947064e-16

# Taylor coefficients for sin(x) through x^19. Folding to [-pi/2, pi/2]
# leaves a truncation remainder below 1e-15, well inside the 1e-12 law.
_C1 = 1.0
_C3 = -0.16666666666666666
_C5 = 0.008333333333333333
_C7 = -0.0001984126984126984
_C9 = 2.7557319223985893e-06
_C11 = -2.505210838544172e-08
_C13 = 1.6059043836821613e-10
_C15 = -7.647163731819816e-13
_C17 = 2.8114572543455206e-15
_C19 = -8.22063524662433e-18


def _reduce_angle(angle: float) -> float:
    if not math.isfinite(angle):
        message = "angle must be finite"
        raise ValueError(message)
    reduced = angle % TAU
    turns = int((angle - reduced) / TAU)
    # TAU is slightly below true 2*pi, so subtract the accumulated tail.
    reduced -= turns * _TAU_TAIL
    if reduced > PI:
        reduced -= TAU
    # sin(pi - x) = sin(x), and the same symmetry holds below -pi/2.
    if reduced > HALF_PI:
        reduced = PI - reduced
    elif reduced < -HALF_PI:
        reduced = -PI - reduced
    return reduced


def sine(angle: float) -> float:
    """Return sine using a fixed polynomial and IEEE operations only."""
    x = _reduce_angle(angle)
    square = x * x
    return x * (
        _C1
        + square
        * (
            _C3
            + square
            * (
                _C5
                + square
                * (
                    _C7
                    + square
                    * (
                        _C9
                        + square
                        * (
                            _C11
                            + square * (_C13 + square * (_C15 + square * (_C17 + square * _C19)))
                        )
                    )
                )
            )
        )
    )


def cosine(angle: float) -> float:
    """Return cosine as a phase-shifted deterministic sine."""
    return sine(angle + HALF_PI)
