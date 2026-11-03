#version 330 core
in vec3 worldPosition;
in vec3 worldNormal;
uniform vec3 cameraPosition;
uniform vec3 baseColor;
uniform float metalness;
uniform float roughness;
uniform float ground;
uniform float time;
uniform mat4 lightViewProjection;
uniform sampler2D shadowMap;
out vec4 color;
const float PI=3.14159265359;

float shadow() {
    vec4 projected=lightViewProjection*vec4(worldPosition,1.0);
    vec3 q=projected.xyz/projected.w*.5+.5;
    if(q.x<0.0 || q.x>1.0 || q.y<0.0 || q.y>1.0)return 0.0;
    float result=0.0;
    for(int x=-2;x<=2;x++)for(int y=-2;y<=2;y++)
        result+=q.z-.002>texture(shadowMap,q.xy+vec2(x,y)/2048.0).r?1.0:0.0;
    return result/25.0;
}
float hexLine(vec2 p) {
    const vec2 scale=vec2(1.0,1.7320508);
    vec2 a=mod(p,scale)-scale*.5;
    vec2 b=mod(p-scale*.5,scale)-scale*.5;
    vec2 cell=dot(a,a)<dot(b,b)?a:b;
    float edge=max(dot(abs(cell),normalize(vec2(1.0,1.7320508))),abs(cell.x));
    return 1.0-smoothstep(.008,.025,abs(edge-.5));
}
vec3 light(vec3 n,vec3 v,vec3 l,vec3 intensity) {
    vec3 h=normalize(v+l);
    float nv=max(dot(n,v),.001),nl=max(dot(n,l),0.0),nh=max(dot(n,h),0.0);
    float a=roughness*roughness,a2=a*a;
    float denom=nh*nh*(a2-1.0)+1.0;
    float d=a2/(PI*denom*denom+.00001);
    float k=(roughness+1.0)*(roughness+1.0)/8.0;
    float g=nv/(nv*(1.0-k)+k)*nl/(nl*(1.0-k)+k);
    vec3 f=mix(vec3(.04),baseColor,metalness);
    f=f+(1.0-f)*pow(1.0-max(dot(h,v),0.0),5.0);
    return ((1.0-f)*(1.0-metalness)*baseColor/PI+d*g*f/(4.0*nv*max(nl,.001)))*intensity*nl;
}
void main() {
    vec3 n=normalize(worldNormal),v=normalize(cameraPosition-worldPosition);
    if(ground>.5) {
        vec2 xy=worldPosition.xy;
        float radial=exp(-length(xy-vec2(67.0,16.0))*.006);
        float grid=hexLine(xy*.055);
        vec3 field=vec3(.012,.025,.019)+vec3(.014,.035,.012)*radial;
        field+=grid*vec3(.018,.038,.015)*(0.3+radial*.7);
        field*=1.0-shadow()*.70;
        color=vec4(field,1.0);return;
    }
    vec3 result=baseColor*.12;
    result+=light(n,v,normalize(vec3(-.4,.65,1.0)),vec3(2.1,2.25,1.85));
    result+=light(n,v,normalize(vec3(.8,-.25,.45)),vec3(.18,.38,.26));
    float rim=pow(1.0-max(dot(n,v),0.0),3.0);
    result+=vec3(.40,.75,.13)*rim*.35;
    // The pulse and inset are illuminated metal; the outside ring stays graphite.
    float luminous=metalness<.85?1.0:.12;
    result+=baseColor*(.20+.04*sin(time*.65))*luminous;
    result=result/(result+vec3(1.0));result=pow(result,vec3(1.0/2.2));
    color=vec4(result*.70,1.0);
}
