#version 330 core
in vec3 worldPosition;
in vec3 worldNormal;
in vec2 textureUV;
uniform vec3 cameraPosition;
uniform vec3 baseColor;
uniform float metalness;
uniform float roughness;
uniform float ground;
uniform float time;
uniform sampler2D shadowMap;
uniform mat4 lightViewProjection;
out vec4 fragColor;
const float PI=3.14159265359;

// Analytic high-dynamic-range studio lighting. Reflection directions are
// evaluated in world space; no downloaded textures or baked object image.
vec3 environment(vec3 r) {
    vec3 studio=mix(vec3(.13,.16,.19),vec3(.8,.82,.78),smoothstep(-.3,.8,r.y));
    float first=pow(max(0.,dot(r,normalize(vec3(-.5,.7,1.)))),38.);
    float strip=pow(max(0.,dot(r,normalize(vec3(.7,.15,.6)))),100.);
    float ceiling=pow(max(0.,dot(r,normalize(vec3(.05,1.,-.1)))),18.);
    return studio+vec3(6.,5.5,4.6)*first+vec3(3.3,4.4,5.)*strip+vec3(3.)*ceiling;
}
vec3 fresnel(float cosine, vec3 f0) { return f0+(1.-f0)*pow(1.-cosine,5.); }
float visibility(vec3 n) {
    vec4 projected=lightViewProjection*vec4(worldPosition,1.);
    vec3 coordinate=projected.xyz/projected.w*.5+.5;
    if(coordinate.z>1. || coordinate.z<0. || any(lessThan(coordinate.xy,vec2(0.))) || any(greaterThan(coordinate.xy,vec2(1.))))return 1.;
    vec2 texel=1./vec2(textureSize(shadowMap,0));
    float bias=max(.0006,.0018*(1.-max(dot(n,normalize(vec3(-.6,.9,1.))),0.)));
    float result=0.;
    for(int x=-2;x<=2;x++)for(int y=-2;y<=2;y++) {
        float stored=texture(shadowMap,coordinate.xy+vec2(x,y)*texel*2.5).r;
        result+=step(coordinate.z-bias,stored);
    }
    return result/25.;
}
vec3 light(vec3 n, vec3 v, vec3 l, vec3 radiance, vec3 f0) {
    vec3 h=normalize(v+l);
    float nv=max(dot(n,v),.001), nl=max(dot(n,l),0.), nh=max(dot(n,h),0.);
    float a=roughness*roughness, a2=a*a;
    float denominator=nh*nh*(a2-1.)+1.;
    float distribution=a2/(PI*denominator*denominator+.0001);
    float k=pow(roughness+1.,2.)/8.;
    float geometry=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));
    vec3 f=fresnel(max(dot(h,v),0.),f0);
    vec3 specular=distribution*geometry*f/(4.*nv*max(nl,.001));
    return ((1.-f)*(1.-metalness)*baseColor/PI+specular)*radiance*nl;
}
void main() {
    vec3 n=normalize(worldNormal),v=normalize(cameraPosition-worldPosition);
    if(!gl_FrontFacing)n=-n;
    vec3 f0=mix(vec3(.04),baseColor,metalness);
    float lit=visibility(n);
    vec3 color=light(n,v,normalize(vec3(-.6,.9,1.)),vec3(3.8,3.4,2.9),f0)*lit;
    color+=light(n,v,normalize(vec3(.8,.3,.5)),vec3(.45,.8,1.3),f0);
    vec3 f=fresnel(max(dot(n,v),0.),f0);
    vec3 reflected=environment(reflect(-v,n));
    vec3 thinFilm=.82+.18*cos(vec3(0.,2.1,4.2)+pow(1.-max(dot(n,v),0.),1.5)*8.);
    color+=reflected*f*mix(vec3(1.),thinFilm,metalness*.6)*(1.-roughness*.65);
    color+=baseColor*(1.-metalness)*environment(n)*.35;
    if(ground>.5) {
        float shadow=exp(-dot(worldPosition.xz,worldPosition.xz)/6800.);
        color=mix(vec3(.82,.79,.73),vec3(.31,.30,.28),clamp(shadow*.18+(1.-lit)*.55,0.,.75));
    }
    // Filmic response retains bright specular edges without clipping labels.
    color=(color*(2.51*color+.03))/(color*(2.43*color+.59)+.14);
    fragColor=vec4(pow(clamp(color,0.,1.),vec3(1./2.2)),1.);
}
