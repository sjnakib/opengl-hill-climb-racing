from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from lib.drawing import drawCircle, drawLine


WINDOW_WIDTH, WINDOW_HEIGHT = 800, 450
BG_COLOR = (0.53, 0.81, 0.98, 1.0)


def init():
    glClearColor(*BG_COLOR)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(175, 1.77, 1, 10)


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(*BG_COLOR)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)

    glColor3f(0.0, 0.0, 0.0)
    drawLine(-200, -100, 200, 100)
    drawCircle(50, 0, 0)

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
