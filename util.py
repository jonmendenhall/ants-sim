import moderngl as mgl
import numpy as np
from pathlib import Path


def load_shader_text(path: Path):
    with open(path, "r") as f:
        return f.read()

def make_quad(ctx, program):
    vertices = np.array([
        # x, y, u, v
        -1.0, -1.0, 0.0, 0.0,
        1.0, -1.0, 1.0, 0.0,
        1.0, 1.0, 1.0, 1.0,
        -1.0, 1.0, 0.0, 1.0,
    ], dtype="f4")

    vbo = ctx.buffer(vertices)
    vao = ctx.vertex_array(program, [
        (vbo, '2f 2f', 'in_pos', 'in_uv'),
    ])
    return vao, vbo