import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QOpenGLWidget, QWidget, QStyle
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QOpenGLVersionProfile, QOpenGLContext
from OpenGL.GL import *
from OpenGL.GLU import *


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.lastPos = QPoint()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / float(height)
        gluPerspective(45, aspect, 1, 100)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslate(0.0, 0.0, -5.0)
        glRotate(self.lastPos.x(), 0.1, 1.0, 0.0)
        glRotate(self.lastPos.y(), 1.0, 0.1, 0.0)
        glBegin(GL_QUADS)

        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        glVertex3f(1.0, 1.0, 1.0)

        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glVertex3f(1.0, 1.0, -1.0)

        glEnd()

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.lastPos = event.pos()
            self.update()


class MainWindow3D(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow3D, self).__init__(parent)
        self.setWindowTitle('MSN Project')
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

        self.glWidget = GLWidget()
        container = QVBoxLayout()
        container.addWidget(self.glWidget)

        centralWidget = QWidget()
        centralWidget.setLayout(container)
        self.setCentralWidget(centralWidget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow3D()
    window.show()
    sys.exit(app.exec_())
