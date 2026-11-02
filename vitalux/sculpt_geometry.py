"""An authored, closed parametric ribbon; native indexed triangle geometry."""
from array import array
from math import sin, cos, pi
from PySide6.QtGui import QVector3D


def mesh(variant=0):
    vertices, indices = array('f'), array('I')
    segments, around = 224, 12
    for i in range(segments+1):
        t = 2*pi*i/segments
        radius = 62 + 18*cos(3*t + variant*0.4)
        center = QVector3D(radius*cos(2*t), radius*sin(2*t), 31*sin(3*t))
        # Numerical tangent + radial frame produces smooth welded normals.
        dt = .0001
        r2 = 62+18*cos(3*(t+dt)+variant*.4)
        next_point = QVector3D(r2*cos(2*(t+dt)), r2*sin(2*(t+dt)), 31*sin(3*(t+dt)))
        tangent = (next_point-center).normalized()
        normal = QVector3D.crossProduct(tangent, QVector3D(0,0,1)).normalized()
        binormal = QVector3D.crossProduct(tangent, normal).normalized()
        for j in range(around+1):
            a = 2*pi*j/around
            # Flattened elliptical cross-section makes a sculpted band.
            offset = normal*(cos(a)*9)+binormal*(sin(a)*3.5)
            point = center+offset
            n = (normal*(cos(a)/9)+binormal*(sin(a)/3.5)).normalized()
            vertices.extend((point.x(),point.y(),point.z(),n.x(),n.y(),n.z(),i/segments,j/around))
    for i in range(segments):
        for j in range(around):
            a=i*(around+1)+j;b=a+around+1
            indices.extend((a,b,a+1,a+1,b,b+1))
    expanded=array('f')
    for index in indices:expanded.extend(vertices[index*8:index*8+8])
    return expanded.tobytes(), len(indices)
