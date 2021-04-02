import sys
from qtmoderngl import QModernGLWidget
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time
import math
import moderngl as mgl
import moderngl_window as mglw
import util
import random


VIEW_SCALE = 1
SCENE_W, SCENE_H = (2560//VIEW_SCALE, 1440//VIEW_SCALE)

NUM_AGENTS = 100000 * 2


class AntsScene:
    def __init__(self, ctx: mgl.Context):
        self.ctx = ctx
        self.quad_program = self.ctx.program(
            vertex_shader="""
            #version 430
            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 uv;
            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
                uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 430
            uniform sampler2D texture0;
            out vec4 fragColor;
            in vec2 uv;
            void main() {
                float value = texture(texture0, uv).x;
                vec3 color = vec3(0.0);
                color = mix(color, vec3(0.0, 0.2, 0.4), smoothstep(0.0, 0.3, value));
                color = mix(color, vec3(0.0, 0.4, 0.4), smoothstep(0.3, 0.90, value));
                color = mix(color, vec3(0.0, 1.0, 0.7), smoothstep(0.90, 0.97, value));
                color = mix(color, vec3(0.0, 1.0, 0.9), smoothstep(0.97, 1.0, value));
                fragColor = vec4(color, 1.0);
            }
            """,
        )
        self.quad_vao, self.quad_vbo = util.make_quad(self.ctx, self.quad_program)
        
        self.agent_shader = self.ctx.compute_shader(util.load_shader_text("agent_shader.hlsl"))
        self.evaporation_shader = self.ctx.compute_shader(util.load_shader_text("evaporation_shader.hlsl"))

        field_data = np.zeros((SCENE_H, SCENE_W), dtype="f4")
        self.field = self.ctx.texture((SCENE_W, SCENE_H), 1, data=field_data, dtype="f4")
        self.field.filter = (mgl.NEAREST, mgl.NEAREST)

        # pattern = 10, 10

        # definitely could use some optimization using numpy operations to act on entire columns of a Nx4 matrix (x,y,angle,0)
        agent_data = []
        for i in range(NUM_AGENTS):
            u = i / NUM_AGENTS * 10
            theta = u * math.pi * 2
            r = random.random() * SCENE_H * 0.5 * 0.2
            x = SCENE_W * 0.5 + math.cos(theta) * r
            y = SCENE_H * 0.5 + math.sin(theta) * r

            # ix = i % pattern[0]
            # iy = (i // pattern[0]) % pattern[1]
            # x = SCENE_W * (0.5 + 0.8 * (ix - (pattern[0] - 1) / 2) / (pattern[0] - 1))
            # y = SCENE_H * (0.5 + 0.5 * (iy - (pattern[1] - 1) / 2) / (pattern[1] - 1))
            # x = 0
            # y = SCENE_H / 2
            # x = random.random() * SCENE_W
            # y = (math.sin(x / SCENE_W * math.pi * 2 * 6) * 0.25 + 0.5 + (random.random() * 2 - 1) * 0.05) * SCENE_H
            angle = theta - math.pi / 2
            # angle = random.random() * 2 * math.pi
            agent_data.append([[x, y, angle, 0]])

        agent_data_bytes = np.array(agent_data).astype("f4").tobytes()
        self.agent_buffer = self.ctx.buffer(agent_data_bytes)


    def render(self, t: float, dt: float):
        self.ctx.clear(0, 0, 0, 1)

        # simulate trail evaporation and diffusion
        try:
            self.evaporation_shader["width"] = SCENE_W
            self.evaporation_shader["height"] = SCENE_H
            self.evaporation_shader["deltaTime"] = dt
            self.evaporation_shader["evaporationSpeed"] = 0.2
            self.evaporation_shader["diffusionSpeed"] = 2
        except Exception:
            pass
        self.field.bind_to_image(0, read=True, write=True)
        self.evaporation_shader.run(math.ceil(SCENE_W / 16), math.ceil(SCENE_H / 16), 1)

        # simulate all ants
        try:
            self.agent_shader["width"] = SCENE_W
            self.agent_shader["height"] = SCENE_H
            self.agent_shader["numAgents"] = NUM_AGENTS
            self.agent_shader["deltaTime"] = dt

            # messing with these parameters can give some interesting diferences in the overall look ;)
            self.agent_shader["moveSpeed"] = 80 # px/s
            self.agent_shader["turnSpeed"] = math.radians(360) # rad/s
            self.agent_shader["sensorAngleOffset"] = math.radians(30) #rad
            self.agent_shader["sensorDistance"] = 45 # px
            
            self.agent_shader["sensorSize"] = 1 # controls kernel size for left, center, right sensors... extra pixels to add on each side of center point
            # 0 = 1x1
            # 1 = 3x3
            # 2 = 5x5
            # 3 = 7x7
            # n = (2n+1)x(2n+1)
            # doesn't really need to be very large to get realistic behavior, just keep relatively small to reduce samples overall

        except Exception as e:
            pass
        self.agent_buffer.bind_to_storage_buffer(0)
        self.agent_shader.run(math.ceil(NUM_AGENTS / 16), 1, 1)

        # draw trail to screen
        self.field.use(location=0)
        self.quad_vao.render(mode=mgl.TRIANGLE_FAN)



class AntsWidget(QModernGLWidget):
    def __init__(self):
        super(AntsWidget, self).__init__()
        self.setWindowTitle("Ants")
        self.scene = None
        self.resize(2560, 1440)
        self.center()

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.updateGL)
        self.timer.start()
        self.t0 = time.time()
        self.frame0_time = 0

    def resizeEvent(self, ev):
        if self.ctx is not None:
            self.ctx.viewport = (0, 0, self.width(), self.height())

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_F11:
            if not self.windowState() & Qt.WindowFullScreen:
                self.showFullScreen()
            else:
                self.showNormal()

    def init(self):
        self.scene = AntsScene(self.ctx)
        self.resizeEvent(None)

    def render(self):
        t = time.time() - self.t0
        self.screen.use()
        self.scene.render(t, max(t - self.frame0_time, 0.001))
        self.frame0_time = t

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


def main():
    app = QApplication(sys.argv)
    widget = AntsWidget()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()