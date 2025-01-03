"""A small 2D hill climb game built with PyOpenGL."""

import math
import random
import time

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from lib.drawing import drawCircle, drawLine


# Window
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 450
BG_COLOR = (0.53, 0.81, 0.98, 1.0)

# Terrain
TERRAIN_LENGTH = 50000
TERRAIN_AMPLITUDE = 70
TERRAIN_ANGLE_STEP = 0.1
TERRAIN_OFFSET_Y = -110
HILL_RENDER_STEP_SIZE = 10

hills = []
collectables = []
terrain_offset_x = 0
start_index = 0
end_index = 0

# Car
CAR_LENGTH = 50
CAR_HEIGHT = 20
WHEEL_RADIUS = 10
CAR_TOP_SPEED = 500
GRAVITY = -100
FRICTION_COEFFICIENT = 0.98

car_front_x = CAR_LENGTH // 2
car_back_x = -CAR_LENGTH // 2
car_front_y = 0
car_back_y = 0
car_velocity_y_front = 0
car_velocity_y_back = 0
car_speed = 0

# Game state
MAX_FUEL = 100
COIN_SCORES = [50, 100, 200, 500, 1000, 5000]
COIN_CHANCE = 0.05
FUEL_CHANCE = 0.01
COLLECTABLE_OFFSET_Y = 30
COIN_RADIUS = 5
FUEL_CAN_HALF_SIZE = 8
AIRTIME_DISPLAY_DURATION = 0.8
AIRTIME_BASE_SCORE = 50
FUEL_DRAIN_RATE = 0.01

fuel_level = MAX_FUEL
score = 0
airtime_start = None
airtime_score = 0
airtime_display_time = 0
game_over = False
paused = False
last_time = time.time()


# Terrain
def generateHills():
    global hills, collectables
    hills = []
    max_hills = TERRAIN_LENGTH // HILL_RENDER_STEP_SIZE
    collectables = [None] * max_hills

    angle = -(math.pi / 2)
    x = 0

    while x <= TERRAIN_LENGTH:
        sin_value = math.sin(angle)

        if sin_value < -0.99:
            rand_limit = random.randint(3, 20)
            for _ in range(rand_limit):
                hills.append(TERRAIN_AMPLITUDE * sin_value + TERRAIN_OFFSET_Y)
                x += HILL_RENDER_STEP_SIZE
        elif sin_value > 0.99:
            rand_limit = random.randint(0, 1)
            for _ in range(rand_limit):
                hills.append(TERRAIN_AMPLITUDE * sin_value + TERRAIN_OFFSET_Y)
                x += HILL_RENDER_STEP_SIZE

        y = TERRAIN_AMPLITUDE * sin_value + TERRAIN_OFFSET_Y
        hills.append(y)

        # Place collectibles randomly along the terrain.
        if random.random() < COIN_CHANCE:
            index = int(x // HILL_RENDER_STEP_SIZE)
            if index < max_hills:
                collectables[index] = "coin"
        elif random.random() < FUEL_CHANCE:
            index = int(x // HILL_RENDER_STEP_SIZE)
            if index < max_hills:
                collectables[index] = "fuel"

        x += HILL_RENDER_STEP_SIZE
        angle += TERRAIN_ANGLE_STEP


def drawHills():
    global start_index, end_index
    glPointSize(2)
    glColor3f(0.01, 0.5, 0.01)

    # Only draw the part of the terrain that is visible.
    view_width = WINDOW_WIDTH
    start_index = max(0, int(terrain_offset_x // HILL_RENDER_STEP_SIZE))
    end_index = min(
        start_index + int(view_width // HILL_RENDER_STEP_SIZE) + 1,
        len(hills) - 1,
    )

    for i in range(start_index, end_index):
        x1 = i * HILL_RENDER_STEP_SIZE - terrain_offset_x - view_width // 2
        y1 = hills[i]
        x2 = (i + 1) * HILL_RENDER_STEP_SIZE - terrain_offset_x - view_width // 2
        y2 = hills[i + 1]
        drawLine(int(x1), int(y1), int(x2), int(y2))


# Car
def drawCar():
    # Body
    glColor3f(0.8, 0.1, 0.1)
    x1, y1 = car_back_x, car_back_y
    x2, y2 = car_front_x, car_front_y
    x3, y3 = car_front_x, car_front_y + CAR_HEIGHT
    x4, y4 = car_back_x, car_back_y + CAR_HEIGHT

    drawLine(int(x1), int(y1), int(x2), int(y2))
    drawLine(int(x2), int(y2), int(x3), int(y3))
    drawLine(int(x3), int(y3), int(x4), int(y4))
    drawLine(int(x4), int(y4), int(x1), int(y1))

    # Wheels
    glColor3f(0.0, 0.0, 0.0)
    drawCircle(WHEEL_RADIUS, car_back_x, car_back_y - WHEEL_RADIUS)
    drawCircle(WHEEL_RADIUS, car_front_x, car_front_y - WHEEL_RADIUS)


def updateCar(delta_time):
    global car_front_y, car_back_y, car_velocity_y_front, car_velocity_y_back, car_speed, terrain_offset_x, fuel_level, score, airtime_start, airtime_score, airtime_display_time, game_over

    if fuel_level <= 0 or paused or game_over:
        return

    # Gravity
    car_velocity_y_front += GRAVITY * delta_time
    car_velocity_y_back += GRAVITY * delta_time
    car_front_y += car_velocity_y_front * delta_time
    car_back_y += car_velocity_y_back * delta_time

    # Friction
    car_speed *= FRICTION_COEFFICIENT

    # Move the terrain under the car.
    new_terrain_offset_x = terrain_offset_x + car_speed * delta_time
    max_offset_x = (len(hills) - 1) * HILL_RENDER_STEP_SIZE - WINDOW_WIDTH

    if new_terrain_offset_x < 0:
        new_terrain_offset_x = 0
    elif new_terrain_offset_x > max_offset_x:
        new_terrain_offset_x = max_offset_x

    terrain_offset_x = new_terrain_offset_x

    # Keep each wheel on top of the terrain.
    front_idx = int(
        (start_index + end_index) / 2
        + ((CAR_LENGTH / 2) / HILL_RENDER_STEP_SIZE)
    )
    back_idx = int(
        (start_index + end_index) / 2
        - ((CAR_LENGTH / 2) / HILL_RENDER_STEP_SIZE)
    )

    front_on_ground = False
    back_on_ground = False

    if 0 <= front_idx < len(hills):
        hill_y_front = hills[front_idx]
        if car_front_y < hill_y_front + WHEEL_RADIUS * 2:
            car_front_y = hill_y_front + WHEEL_RADIUS * 2
            car_velocity_y_front = 0
            front_on_ground = True

    if 0 <= back_idx < len(hills):
        hill_y_back = hills[back_idx]
        if car_back_y < hill_y_back + WHEEL_RADIUS * 2:
            car_back_y = hill_y_back + WHEEL_RADIUS * 2
            car_velocity_y_back = 0
            back_on_ground = True

    # Award airtime points once per full second in the air.
    if not front_on_ground and not back_on_ground:
        if airtime_start is None:
            airtime_start = time.time()
        else:
            airtime_duration = time.time() - airtime_start
            if airtime_duration >= 1:
                airtime_score = AIRTIME_BASE_SCORE * (2 ** (int(airtime_duration) - 1))
                score += airtime_score
                airtime_display_time = time.time()
                airtime_start = time.time()
    else:
        airtime_start = None

    # Burn fuel while the car is moving.
    fuel_level -= abs(car_speed) * delta_time * FUEL_DRAIN_RATE

    if fuel_level <= 0:
        game_over = True
        print("Game over! Fuel depleted! Score:", score)


# Collectibles
def drawCollectibles():
    for i in range(start_index, end_index):
        collectable = collectables[i]
        if collectable is None:
            continue

        cx = i * HILL_RENDER_STEP_SIZE - terrain_offset_x - WINDOW_WIDTH // 2
        cy = hills[i] + COLLECTABLE_OFFSET_Y

        if collectable == "coin":
            glColor3f(1.0, 0.84, 0.0)
            drawCircle(COIN_RADIUS, int(cx), int(cy))
        elif collectable == "fuel":
            glColor3f(1.0, 0.0, 0.0)
            x1, y1 = int(cx - FUEL_CAN_HALF_SIZE), int(cy - FUEL_CAN_HALF_SIZE)
            x2, y2 = int(cx + FUEL_CAN_HALF_SIZE), int(cy - FUEL_CAN_HALF_SIZE)
            x3, y3 = int(cx + FUEL_CAN_HALF_SIZE), int(cy + FUEL_CAN_HALF_SIZE)
            x4, y4 = int(cx - FUEL_CAN_HALF_SIZE), int(cy + FUEL_CAN_HALF_SIZE)
            drawLine(x1, y1, x2, y2)
            drawLine(x2, y2, x3, y3)
            drawLine(x3, y3, x4, y4)
            drawLine(x4, y4, x1, y1)


def checkCollectibleCollision():
    global fuel_level, score

    for i in range(start_index, end_index):
        collectable = collectables[i]
        if collectable is None:
            continue

        cx = i * HILL_RENDER_STEP_SIZE - terrain_offset_x - WINDOW_WIDTH // 2
        cy = hills[i] + COLLECTABLE_OFFSET_Y

        car_left = car_front_x - CAR_LENGTH // 2
        car_right = car_front_x + CAR_LENGTH // 2
        car_bottom = min(car_back_y, car_front_y) - WHEEL_RADIUS
        car_top = max(car_back_y, car_front_y) + WHEEL_RADIUS

        if (
            cx >= car_left and cx <= car_right and
            cy >= car_bottom and cy <= car_top
        ):
            if collectable == "coin":
                score += random.choice(COIN_SCORES)
                print(f"Coin collected! Score: {score}")
            elif collectable == "fuel":
                fuel_level = MAX_FUEL
                print(f"Fuel collected! Fuel level: {fuel_level}")

            collectables[i] = None


# HUD
def renderText(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))


def displayFuelLevel():
    glColor3f(0, 0, 0)
    renderText(
        -WINDOW_WIDTH // 2 + 10,
        WINDOW_HEIGHT // 2 - 20,
        f"Fuel: {int(fuel_level)} L",
    )


def displayCarSpeedAndGear():
    glColor3f(0, 0, 0)
    renderText(
        -WINDOW_WIDTH // 2 + 10,
        -WINDOW_HEIGHT // 2 + 20,
        f"Speed: {int(abs(car_speed // 10) * 3.6)} km/h",
    )

    gear = "Forward" if car_speed > 0 else "Reverse" if car_speed < 0 else "Neutral"
    renderText(WINDOW_WIDTH // 2 - 150, -WINDOW_HEIGHT // 2 + 20, f"Gear: {gear}")


def displayScore():
    glColor3f(0, 0, 0)
    renderText(
        -WINDOW_WIDTH // 2 + 10,
        WINDOW_HEIGHT // 2 - 40,
        f"Score: {int(score)}",
    )


def displayDistanceTravelled():
    glColor3f(0, 0, 0)
    renderText(
        -WINDOW_WIDTH // 2 + 10,
        WINDOW_HEIGHT // 2 - 60,
        f"Travelled: {int(terrain_offset_x // 10)} m",
    )


def displayAirtimeScore():
    if time.time() - airtime_display_time < AIRTIME_DISPLAY_DURATION:
        glColor3f(0, 0, 0)
        renderText(-50, 0, f"Airtime +{int(airtime_score)}")


def displayGameOver():
    # Blink the message every half second.
    if int(time.time() * 2) % 2 == 0:
        glColor3f(1, 0, 0)
        renderText(-50, 0, "Game Over!", font=GLUT_BITMAP_HELVETICA_18)
        renderText(-50, -30, f"Final Score: {int(score)}", font=GLUT_BITMAP_HELVETICA_18)


def displayPaused():
    glColor3f(1, 1, 0)
    renderText(-50, 0, "Game Paused", font=GLUT_BITMAP_HELVETICA_18)


# Input
def keyboardListener(key, x, y):
    global car_speed, paused

    if key == b'\x1b':
        glutLeaveMainLoop()
    elif key == b'a':
        if not paused and not game_over:
            car_speed = -CAR_TOP_SPEED
    elif key == b'd':
        if not paused and not game_over:
            car_speed = CAR_TOP_SPEED
    elif key == b' ':
        if not game_over:
            paused = not paused
            print("Game paused!" if paused else "Game resumed!")
    elif key == b'r':
        restartGame()

    glutPostRedisplay()


def restartGame():
    global car_front_y, car_back_y, car_velocity_y_front, car_velocity_y_back, car_speed, fuel_level, score, airtime_start, airtime_score, airtime_display_time, game_over, paused, terrain_offset_x, last_time

    car_front_y = 0
    car_back_y = 0
    car_velocity_y_front = 0
    car_velocity_y_back = 0
    car_speed = 0
    fuel_level = MAX_FUEL
    score = 0
    airtime_start = None
    airtime_score = 0
    airtime_display_time = 0
    game_over = False
    paused = False
    terrain_offset_x = 0
    last_time = time.time()
    generateHills()


# Game loop
def init():
    glClearColor(*BG_COLOR)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(175, 1.77, 1, 10)

    generateHills()


def animate():
    global last_time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    updateCar(delta_time)
    checkCollectibleCollision()

    glutPostRedisplay()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)

    drawHills()

    if game_over:
        displayGameOver()
    elif paused:
        displayPaused()

    drawCar()
    drawCollectibles()
    displayFuelLevel()
    displayCarSpeedAndGear()
    displayScore()
    displayDistanceTravelled()
    displayAirtimeScore()

    glutSwapBuffers()


if __name__ == "__main__":
    glutInit()
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)

    glutCreateWindow(b"Hill Climb Racing (Simple)")
    init()

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboardListener)
    glutIdleFunc(animate)

    glutMainLoop()
