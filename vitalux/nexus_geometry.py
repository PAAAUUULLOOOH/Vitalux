"""Extruded Vitalux ring and the original seven-segment heartbeat silhouette."""
from array import array
from math import cos,sin,pi

PULSE=((318,616),(439,616),(532,501),(642,783),(777,458),(849,616),(939,616))


def _vertex(out,point,normal):out.extend((*point,*normal,0.,0.))


def rings(radius=125.,width=7.,depth=10.,arcs=((8,149),(158,303),(313,350))):
    out=array('f');inner,outer=radius-width/2,radius+width/2
    for start,end in arcs:
        steps=max(3,round((end-start)/2))
        for n in range(steps):
            a,b=(v*pi/180 for v in (start+(end-start)*n/steps,start+(end-start)*(n+1)/steps))
            for z,nz,reverse in ((depth/2,1,False),(-depth/2,-1,True)):
                points=[(inner*cos(a),inner*sin(a),z),(outer*cos(a),outer*sin(a),z),
                        (outer*cos(b),outer*sin(b),z),(inner*cos(b),inner*sin(b),z)]
                for i in ((0,2,1,0,3,2) if reverse else (0,1,2,0,2,3)):_vertex(out,points[i],(0,0,nz))
            for r,sign in ((inner,-1),(outer,1)):
                points=[(r*cos(a),r*sin(a),-depth/2),(r*cos(a),r*sin(a),depth/2),
                        (r*cos(b),r*sin(b),depth/2),(r*cos(b),r*sin(b),-depth/2)]
                for i in (0,1,2,0,2,3):
                    angle=a if i<2 else b
                    _vertex(out,points[i],(sign*cos(angle),sign*sin(angle),0))
        for angle,sign in ((start*pi/180,-1),(end*pi/180,1)):
            points=[(inner*cos(angle),inner*sin(angle),-depth/2),(outer*cos(angle),outer*sin(angle),-depth/2),
                    (outer*cos(angle),outer*sin(angle),depth/2),(inner*cos(angle),inner*sin(angle),depth/2)]
            for i in (0,1,2,0,2,3):_vertex(out,points[i],(-sign*sin(angle),sign*cos(angle),0))
    return out.tobytes(),len(out)//8


def pulse():
    out=array('f');points=[((x-628)*.30,(628-y)*.30,0.) for x,y in PULSE]
    radius=7.2;around=16
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
        nx,ny=-dy/length,dx/length
        for j in range(around):
            angles=(2*pi*j/around,2*pi*(j+1)/around)
            normals=[(nx*cos(t),ny*cos(t),sin(t)) for t in angles]
            quad=[tuple(p[k]+radius*n[k] for k in range(3)) for p,n in
                  ((a,normals[0]),(b,normals[0]),(b,normals[1]),(a,normals[1]))]
            for i in (0,1,2,0,2,3):_vertex(out,quad[i],normals[0 if i<2 else 1])
    # Spherical joins reproduce the original logo's round stroke corners.
    for center in points:
        for latitude in range(8):
            for longitude in range(around):
                normals=[]
                for u,v in ((latitude,longitude),(latitude,longitude+1),(latitude+1,longitude+1),(latitude+1,longitude)):
                    a=-pi/2+pi*u/8;b=2*pi*v/around
                    normals.append((cos(a)*cos(b),cos(a)*sin(b),sin(a)))
                for i in (0,1,2,0,2,3):
                    n=normals[i];_vertex(out,tuple(center[k]+radius*n[k] for k in range(3)),n)
    return out.tobytes(),len(out)//8


def field():
    out=array('f')
    for x,y in ((-1500,-1000),(1500,-1000),(-1500,1000),(-1500,1000),(1500,-1000),(1500,1000)):
        _vertex(out,(x,y,-95.),(0.,0.,1.))
    return out.tobytes(),6
