import math
import random
import time

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from lib.drawing import drawCircle, drawLine


WINDOW_WIDTH, WINDOW_HEIGHT = 800, 450
BG_COLOR = (0.53, 0.81, 0.98, 1.0)

hills = []
collectables = []
hill_render_step_size = 10
terrain_offset_x = 0
start_index = 0
end_index = 0

car_length = 50
car_front_x = car_length // 2
car_back_x = -car_length // 2
car_front_y = 0
car_back_y = 0
car_velocity_y_front = 0
car_velocity_y_back = 0
car_height = 20
wheel_radius = 10
car_speed = 0
car_top_speed = 500
gravity = -100
fuel_level = 100
score = 0
paused = False
last_time = time.time()


def generateHills():
    global hills, hill_render_step_size, collectables
    hills = []
    max_hills = 50000 // hill_render_step_size
    collectables = [None] * max_hills

    amplitude = 70
    angle_inc = 0.1
    angle = -(math.pi / 2)
    offset_y = -110

    x = 0
    while x <= 50000:
        sin = math.sin(angle)
        if sin < -0.99:
            rand_limit = random.randint(3, 20)
            for _ in range(rand_limit):
                hills.append(amplitude * sin + offset_y)
                x += hill_render_step_size
        elif sin > 0.99:
            rand_limit = random.randint(0, 1)
            for _ in range(rand_limit):
                hills.append(amplitude * sin + offset_y)
                x += hill_render_step_size

        y = amplitude * sin + offset_y
        hills.append(y)

        # Generate collectibles randomly
        if random.random() < 0.05:
            index = int(x // hill_render_step_size)
            if index < max_hills:
                collectable_type = "coin"
                collectables[index] = collectable_type
        elif random.random() < 0.01:
            index = int(x // hill_render_step_size)
            if index < max_hills:
                collectable_type = "fuel"
                collectables[index] = collectable_type

        x += hill_render_step_size
        angle += angle_inc


def drawHills():
    global hills, hill_render_step_size, terrain_offset_x, WINDOW_WIDTH, start_index, end_index
    glPointSize(2)
    glColor3f(0.01, 0.5, 0.01)

    # Only draw the part that is visible in the viewing area
    view_width = WINDOW_WIDTH
    start_index = max(0, int(terrain_offset_x // hill_render_step_size))
    end_index = min(start_index + int(view_width // hill_render_step_size) + 1, len(hills) - 1)

    for i in range(start_index, end_index):
        x1 = i * hill_render_step_size - terrain_offset_x - view_width // 2
        y1 = hills[i]
        x2 = (i + 1) * hill_render_step_size - terrain_offset_x - view_width // 2
        y2 = hills[i + 1]
        drawLine(int(x1), int(y1), int(x2), int(y2))


def drawCar():
    global car_front_x, car_front_y, car_back_x, car_back_y, car_height, wheel_radius

    # Draw the car body
    glColor3f(0.8, 0.1, 0.1)
    x1, y1 = car_back_x, car_back_y
    x2, y2 = car_front_x, car_front_y
    x3, y3 = car_front_x, car_front_y + car_height
    x4, y4 = car_back_x, car_back_y + car_height

    drawLine(int(x1), int(y1), int(x2), int(y2))
    drawLine(int(x2), int(y2), int(x3), int(y3))
    drawLine(int(x3), int(y3), int(x4), int(y4))
    drawLine(int(x4), int(y4), int(x1), int(y1))

    # Draw the wheels
    glColor3f(0.0, 0.0, 0.0)
    drawCircle(wheel_radius, car_back_x, car_back_y - wheel_radius)
    drawCircle(wheel_radius, car_front_x, car_front_y - wheel_radius)


def drawCollectibles():
    global collectables, terrain_offset_x, start_index, end_index

    for i in range(start_index, end_index):
        collectable = collectables[i]
        if collectable is None:
            continue

        cx = i * hill_render_step_size - terrain_offset_x - WINDOW_WIDTH // 2
        cy = hills[i] + 30

        if collectable == "coin":
            glColor3f(1.0, 0.84, 0.0)
            drawCircle(5, int(cx), int(cy))
        elif collectable == "fuel":
            glColor3f(1.0, 0.0, 0.0)
            x1, y1 = int(cx - 8), int(cy - 8)
            x2, y2 = int(cx + 8), int(cy - 8)
            x3, y3 = int(cx + 8), int(cy + 8)
            x4, y4 = int(cx - 8), int(cy + 8)
            drawLine(x1, y1, x2, y2)
            drawLine(x2, y2, x3, y3)
            drawLine(x3, y3, x4, y4)
            drawLine(x4, y4, x1, y1)


def checkCollectibleCollision():
    global collectables, car_front_x, car_front_y, car_back_x, car_back_y, fuel_level, score, terrain_offset_x, car_length, wheel_radius, start_index, end_index

    for i in range(start_index, end_index):
        collectable = collectables[i]
        if collectable is None:
            continue

        cx = i * hill_render_step_size - terrain_offset_x - WINDOW_WIDTH // 2
        cy = hills[i] + 30

        car_left = car_front_x - car_length // 2
        car_right = car_front_x + car_length // 2
        car_bottom = min(car_back_y, car_front_y) - wheel_radius
        car_top = max(car_back_y, car_front_y) + wheel_radius

        if (
            cx >= car_left and cx <= car_right and
            cy >= car_bottom and cy <= car_top
        ):
            if collectable == "coin":
                coin_score = random.choice([50, 100, 200, 500, 1000, 5000])
                score += coin_score
                print(f"Coin collected! Score: {score}")
            elif collectable == "fuel":
                fuel_level = 100
                print(f"Fuel collected! Fuel level: {fuel_level}")

            collectables[i] = None


def updateCar(delta_time):
    global car_front_y, car_back_y, car_velocity_y_front, car_velocity_y_back, gravity, start_index, end_index, wheel_radius, car_length, hill_render_step_size, car_speed, terrain_offset_x

    if paused:
        return

    # Gravity on the front and rear wheels
    car_velocity_y_front += gravity * delta_time
    car_velocity_y_back += gravity * delta_time
    car_front_y += car_velocity_y_front * delta_time
    car_back_y += car_velocity_y_back * delta_time

    # Apply friction
    friction_coefficient = 0.98
    car_speed *= friction_coefficient

    # Move the terrain under the car
    new_terrain_offset_x = terrain_offset_x + car_speed * delta_time

    max_offset_x = (len(hills) - 1) * hill_render_step_size - WINDOW_WIDTH
    if new_terrain_offset_x < 0:
        new_terrain_offset_x = 0
    elif new_terrain_offset_x > max_offset_x:
        new_terrain_offset_x = max_offset_x

    terrain_offset_x = new_terrain_offset_x

    # Find the terrain height under each wheel
    front_idx = int((start_index + end_index) / 2 + ((car_length / 2) / hill_render_step_size))
    back_idx = int((start_index + end_index) / 2 - ((car_length / 2) / hill_render_step_size))

    if 0 <= front_idx < len(hills):
        hill_y_front = hills[front_idx]

        if car_front_y < hill_y_front + wheel_radius * 2:
            car_front_y = hill_y_front + wheel_radius * 2
            car_velocity_y_front = 0

    if 0 <= back_idx < len(hills):
        hill_y_back = hills[back_idx]

        if car_back_y < hill_y_back + wheel_radius * 2:
            car_back_y = hill_y_back + wheel_radius * 2
            car_velocity_y_back = 0


def keyboardListener(key, x, y):
    global car_speed, paused

    if key == b'\x1b':
        glutLeaveMainLoop()

    elif key == b'a':
        car_speed = -car_top_speed

    elif key == b'd':
        car_speed = car_top_speed

    elif key == b' ':
        paused = not paused
        print("Game paused!" if paused else "Game resumed!")

    elif key == b'r':
        restartGame()

    glutPostRedisplay()


def restartGame():
    global car_front_x, car_front_y, car_back_x, car_back_y, car_velocity_y_front, car_velocity_y_back, car_speed, fuel_level, score, paused, terrain_offset_x, last_time
    car_front_x = car_length // 2
    car_back_x = -car_length // 2
    car_front_y = 0
    car_back_y = 0
    car_velocity_y_front = 0
    car_velocity_y_back = 0
    car_speed = 0
    fuel_level = 100
    score = 0
    paused = False
    terrain_offset_x = 0
    last_time = time.time()
    generateHills()


def renderText(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))


def displayPaused():
    glColor3f(1, 1, 0)
    renderText(-50, 0, "Game Paused", font=GLUT_BITMAP_HELVETICA_18)


def displayFuelLevel():
    global fuel_level
    glColor3f(0, 0, 0)
    renderText(-WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT // 2 - 20, f"Fuel: {int(fuel_level)} L")


def displayCarSpeedAndGear():
    global car_speed
    glColor3f(0, 0, 0)
    renderText(-WINDOW_WIDTH // 2 + 10, -WINDOW_HEIGHT // 2 + 20, f"Speed: {int(abs(car_speed//10)*3.6)} km/h")

    gear = "Forward" if car_speed > 0 else "Reverse" if car_speed < 0 else "Neutral"
    renderText(WINDOW_WIDTH // 2 - 150, -WINDOW_HEIGHT // 2 + 20, f"Gear: {gear}")


def animate():
    global last_time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    updateCar(delta_time)
    checkCollectibleCollision()

    glutPostRedisplay()


def init():
    glClearColor(*BG_COLOR)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(175, 1.77, 1, 10)

    generateHills()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(*BG_COLOR)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)

    drawHills()

    if paused:
        displayPaused()

    drawCar()
    drawCollectibles()
    displayFuelLevel()
    displayCarSpeedAndGear()

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
