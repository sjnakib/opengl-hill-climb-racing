# 🚗 Hill Climb Racing (Simplified)

A small 2D hill climb game where you drive over random hills, collect coins, and keep the fuel tank from running dry.

[![Stars](https://img.shields.io/github/stars/sjnakib/opengl-hill-climb-racing?style=for-the-badge&logo=github&color=yellow)](https://github.com/sjnakib/opengl-hill-climb-racing/stargazers)
[![Forks](https://img.shields.io/github/forks/sjnakib/opengl-hill-climb-racing?style=for-the-badge&logo=github&color=blue)](https://github.com/sjnakib/opengl-hill-climb-racing/network/members)
[![Last commit](https://img.shields.io/github/last-commit/sjnakib/opengl-hill-climb-racing?style=for-the-badge&color=green)](https://github.com/sjnakib/opengl-hill-climb-racing/commits/main)
[![Top language](https://img.shields.io/github/languages/top/sjnakib/opengl-hill-climb-racing?style=for-the-badge)](https://github.com/sjnakib/opengl-hill-climb-racing)
[![License](https://img.shields.io/github/license/sjnakib/opengl-hill-climb-racing?style=for-the-badge)](https://github.com/sjnakib/opengl-hill-climb-racing/blob/main/LICENSE)

## About

This project is a simplified version of Hill Climb Racing, built for CSE423: Computer Graphics at BRAC University. The game draws the terrain, car, coins, and fuel cans with OpenGL primitives and midpoint line and circle algorithms. The car follows the hills, uses fuel while driving, and scores points for coins and airtime.

## Features

- Randomly generated hills with coins and fuel cans
- Car physics with gravity, friction, and separate front and rear wheel physics
- Fuel, speed, gear, score, and distance display
- Airtime bonus points and a game over screen
- Pause, restart, and keyboard controls

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenGL](https://img.shields.io/badge/OpenGL-5586A4?style=for-the-badge&logo=opengl&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)

## Getting Started

You need Python 3 and freeglut. If freeglut is missing, install it with your package manager. For example, on Debian or Ubuntu:

```bash
sudo apt install freeglut3-dev
```

On Arch Linux:

```bash
sudo pacman -S freeglut
```

Create a virtual environment and install the Python dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the game:

```bash
python hill_climb.py
```

On a Wayland session, use the GLX backend:

```bash
PYOPENGL_PLATFORM=glx python hill_climb.py
```

## Usage

Drive with the keyboard:

| Key | Action |
| --- | --- |
| `A` | Drive left |
| `D` | Drive right |
| `Space` | Pause or resume |
| `R` | Restart |
| `Esc` | Quit |

Press `D` to drive right. The car moves over the hills, the fuel gauge drops, and the distance counter goes up. Collect a coin to add a random amount from 50 to 5000 points. Collect a fuel can to refill the tank to 100 L. If the fuel reaches 0, the game ends and shows your final score.

## Project Structure

```text
.
├── hill_climb.py                # Main game loop, physics, HUD, and input
├── lib/
│   ├── __init__.py
│   └── drawing.py               # Midpoint line and circle drawing helpers
├── docs/
│   └── game-specification.docx  # Assignment brief
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT license
└── README.md
```

## Authors

- Shafaat Jamil Nakib
- A.B.M Danial
- Rabaya Farzana Sikder

## License

MIT License. See [LICENSE](LICENSE) for the full text.
