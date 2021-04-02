#version 430


#define PI 3.14159265
#define EDGE 0.1
#define EDGE_INV (1 - EDGE)

struct Agent {
    vec4 pos;
};


layout (local_size_x = 16, local_size_y = 1) in;

layout(r32f, location=0) uniform image2D field;
uniform uint width;
uniform uint height;
uniform uint numAgents;
uniform float deltaTime;
uniform float moveSpeed;
uniform float turnSpeed;
uniform int sensorSize;
uniform float sensorDistance;
uniform float sensorAngleOffset;

layout(std430, binding=0) buffer agents_in { Agent agents[]; };




uint hash(uint s) {
    s ^= 2747636419u;
    s *= 2654435769u;
    s ^= s >> 16;
    s *= 2654435769u;
    s ^= s >> 16;
    s *= 2654435769u;
    return s;
}

float random(uint s) {
    return float(hash(s)) / 4294967295.0;
}


float sense(Agent agent, float angleOffset) {
    float sensorAngle = agent.pos.z + angleOffset;
    vec2 sensorDir = vec2(cos(sensorAngle), sin(sensorAngle));
    ivec2 sensorCenter = ivec2(agent.pos.xy + sensorDir * sensorDistance);
    
    float sum = 0.0;
    for(int ox = -sensorSize; ox <= sensorSize; ox++) {
        for(int oy = -sensorSize; oy <= sensorSize; oy++) {
            sum += imageLoad(field, sensorCenter + ivec2(ox, oy)).x;
        }
    }
    return sum;
}


void main() {
    uint id = gl_GlobalInvocationID.x;
    if(id >= numAgents)
        return;
    
    Agent agent = agents[id];
    float random = random(uint(agent.pos.x * width + agent.pos.y) + hash(id));

    float sForward = sense(agent, 0.0);
    float sRight = sense(agent, -sensorAngleOffset);
    float sLeft = sense(agent, sensorAngleOffset);


    if(sForward >= sLeft && sForward >= sRight) {
        // keep going forward
        agent.pos.z += (random - 0.5) * 0.05 * turnSpeed * deltaTime;
    } else if(sForward < sLeft && sForward < sRight) {
        agent.pos.z += (random - 0.5) * 2.0 * turnSpeed * deltaTime;
    } else if(sRight > sLeft) {
        agent.pos.z -= turnSpeed * deltaTime;
    } else if(sLeft > sRight) {
        agent.pos.z += turnSpeed * deltaTime;
    }

    vec2 vel = vec2(cos(agent.pos.z), sin(agent.pos.z));
    vec2 newPos = agent.pos.xy + vel * moveSpeed * deltaTime;

    if(newPos.x <= 0 || newPos.x >= width || newPos.y <= 0 || newPos.y >= height) {
        newPos.x = min(max(newPos.x, 0), width);
        newPos.y = min(max(newPos.y, 0), height);
        agent.pos.z = random * 2 * PI;
    }

    if(newPos.x <= float(width) * EDGE || newPos.x >= float(width) * EDGE_INV || newPos.y <= float(height) * EDGE  || newPos.y >= float(height) * EDGE_INV) {
        vec2 center = vec2(float(width) * 0.5, float(height) * 0.5);
        vec2 towardCenter = normalize(center - agent.pos.xy);
        float d = towardCenter.y * vel.x - towardCenter.x * vel.y;
        agent.pos.z += d * turnSpeed * 0.2 * deltaTime;
    }

    agent.pos.xy = newPos;
    agents[id] = agent;

    imageStore(
        field,
        ivec2(agent.pos.xy),
        vec4(
            1.0,
            0.0,
            0.0,
            1.0
        )
    );

}