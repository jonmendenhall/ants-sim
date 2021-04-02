from PyQt5 import QtGui, QtWidgets, QtCore, QtOpenGL
import moderngl



class QModernGLWidget(QtOpenGL.QGLWidget):
    ctx = None

    def __init__(self):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(4, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)

        # disable v-sync to have unbounded FPS if you don't mind potential tearing
        # fmt.setSwapInterval(0)
        
        super(QModernGLWidget, self).__init__(fmt, None)

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.screen = self.ctx.detect_framebuffer()
        self.init()

    def paintGL(self):
        self.render()

    def init(self):
        pass

    def render(self):
        pass