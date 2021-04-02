#version 430


layout(local_size_x = 16, local_size_y = 16) in;

layout(r32f, location=0) uniform image2D field;
uniform uint width;
uniform uint height;
uniform float deltaTime;
uniform float evaporationSpeed;
uniform float diffusionSpeed;


void main() {
    ivec2 id = ivec2(gl_GlobalInvocationID.xy);
    if(id.x < 0 || id.y < 0 || id.x >= width || id.y >= height)
        return;

    float value = imageLoad(field, id).x;

    float sum = 0.0;
    for(int ox = -1; ox <= 1; ox++) {
        for(int oy = -1; oy <= 1; oy++) {
            int sx = id.x + ox;
            int sy = id.y + oy;
            sum += imageLoad(field, ivec2(sx, sy)).x;
        }
    }
    float blurValue = sum / 9.0;

    value = mix(value, blurValue, diffusionSpeed * deltaTime);
    value = max(0, value - evaporationSpeed * deltaTime);

    imageStore(
        field,
        id,
        vec4(value, 0.0, 0.0, 1.0)
    );

}