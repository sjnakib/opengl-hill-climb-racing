import math
import random

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from lib.drawing import drawCircle, drawLine


WINDOW_WIDTH, WINDOW_HEIGHT = 800, 450
BG_COLOR = (0.53, 0.81, 0.98, 1.0)

hills = []
hill_render_step_size = 10
terrain_offset_x = 0


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
    global hills, hill_render_step_size, terrain_offset_x, WINDOW_WIDTH
    glPointSize(2)
    glColor3f(0.01, 0.5, 0.01)

    for i in range(len(hills) - 1):
        x1 = i * hill_render_step_size - terrain_offset_x - WINDOW_WIDTH // 2
        y1 = hills[i]
        x2 = (i + 1) * hill_render_step_size - terrain_offset_x - WINDOW_WIDTH // 2
        y2 = hills[i + 1]
        drawLine(int(x1), int(y1), int(x2), int(y2))


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

    glutSwapBuffers()


if __name__ == "__main__":
    glutInit()
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)

    glutCreateWindow(b"Hill Climb Racing (Simple)")
    init()

    glutDisplayFunc(display)

    glutMainLoop()
