#version 330 core
layout(location=0) in vec3 position;
layout(location=1) in vec3 normal;
layout(location=2) in vec2 uv;
uniform mat4 model;
uniform mat4 viewProjection;
uniform mat3 normalMatrix;
out vec3 worldPosition;
out vec3 worldNormal;
out vec2 textureUV;
void main() {
    vec4 world=model*vec4(position,1.0);
    worldPosition=world.xyz;
    worldNormal=normalize(normalMatrix*normal);
    textureUV=uv;
    gl_Position=viewProjection*world;
}
