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
gravity = -100
last_time = time.time()


def generateHills():
    global hills, hill_render_step_size
    hills = []

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


def updateCar(delta_time):
    global car_front_y, car_back_y, car_velocity_y_front, car_velocity_y_back, gravity, start_index, end_index, wheel_radius, car_length, hill_render_step_size

    # Gravity on the front and rear wheels
    car_velocity_y_front += gravity * delta_time
    car_velocity_y_back += gravity * delta_time
    car_front_y += car_velocity_y_front * delta_time
    car_back_y += car_velocity_y_back * delta_time

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


def animate():
    global last_time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    updateCar(delta_time)

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
    drawCar()

    glutSwapBuffers()


if __name__ == "__main__":
    glutInit()
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)

    glutCreateWindow(b"Hill Climb Racing (Simple)")
    init()

    glutDisplayFunc(display)
    glutIdleFunc(animate)

    glutMainLoop()
