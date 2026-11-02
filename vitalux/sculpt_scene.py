"""Authored OpenGL 3.3 geometry and physical materials; no external 3D engine."""
from pathlib import Path
from array import array
import time
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QMatrix4x4, QSurfaceFormat, QVector3D
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram,
    QOpenGLVertexArrayObject, QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile,
    QOpenGLFramebufferObject,QOpenGLFramebufferObjectFormat)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication, QWidget
from . import motion
from .sculpt_geometry import mesh


class SculptView(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        fmt=QSurfaceFormat();fmt.setVersion(3,3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setSamples(4);fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
        self.started=time.monotonic();self.phase=0.;self.pointer=[0.,0.];self.load=0.
        self.ready=False;self.error='';self.buffers=[];self.program=None
        self.shadow_target=None;self.shadow_program=None
        self.timer=QTimer(self);self.timer.setInterval(16);self.timer.timeout.connect(self.advance)
        self.setAttribute(Qt.WA_TransparentForMouseEvents,True)

    def initializeGL(self):
        try:
            profile=QOpenGLVersionProfile();profile.setVersion(3,3);profile.setProfile(QSurfaceFormat.CoreProfile)
            self.gl=QOpenGLVersionFunctionsFactory.get(profile,self.context())
            if self.gl is None:raise RuntimeError('OpenGL 3.3 unavailable')
            self.gl.initializeOpenGLFunctions()
            self.context().aboutToBeDestroyed.connect(self.cleanup,Qt.DirectConnection)
            self.program=QOpenGLShaderProgram(self)
            assets=Path(__file__).resolve().parents[1]/'assets/sculpt'
            for kind,name in ((QOpenGLShader.Vertex,'material.vert'),(QOpenGLShader.Fragment,'material.frag')):
                if not self.program.addShaderFromSourceFile(kind,str(assets/name)):
                    raise RuntimeError(self.program.log())
            if not self.program.link():raise RuntimeError(self.program.log())
            self.program.bind()
            self.locations={name:self.program.uniformLocation(name) for name in
                ('viewProjection','cameraPosition','time','model','normalMatrix','baseColor','metalness','roughness','ground','lightViewProjection','shadowMap')}
            for variant in range(3):self._upload(*mesh(variant))
            plane=array('f')
            for x,z in ((-1000,-1000),(-1000,1000),(1000,-1000),(1000,-1000),(-1000,1000),(1000,1000)):
                plane.extend((x,-102,z,0,1,0,0,0))
            self._upload(plane.tobytes(),6)
            self.program.release()
            self.shadow_program=QOpenGLShaderProgram(self)
            for kind,name in ((QOpenGLShader.Vertex,'material.vert'),(QOpenGLShader.Fragment,'shadow.frag')):
                if not self.shadow_program.addShaderFromSourceFile(kind,str(assets/name)):raise RuntimeError(self.shadow_program.log())
            if not self.shadow_program.link():raise RuntimeError(self.shadow_program.log())
            target_format=QOpenGLFramebufferObjectFormat()
            target_format.setAttachment(QOpenGLFramebufferObject.Depth)
            target_format.setInternalTextureFormat(0x822E)  # R32F depth values
            self.shadow_target=QOpenGLFramebufferObject(2048,2048,target_format)
            if not self.shadow_target.isValid():raise RuntimeError('Shadow framebuffer unavailable')
            self.ready=True
            print('Vitalux: native 3D surface initialized',flush=True)
        except Exception as exc:
            self.error=str(exc);self.ready=False
            print('Vitalux: 3D surface unavailable:',self.error,flush=True)

    def _upload(self, data, count):
        vao=QOpenGLVertexArrayObject(self);vao.create();vao.bind()
        buffer=QOpenGLBuffer(QOpenGLBuffer.VertexBuffer);buffer.create();buffer.bind()
        buffer.allocate(data,len(data))
        for location,offset,size in ((0,0,3),(1,12,3),(2,24,2)):
            self.program.enableAttributeArray(location)
            self.program.setAttributeBuffer(location,0x1406,offset,size,32)
        vao.release();buffer.release()
        self.buffers.append((vao,buffer,count))

    def paintGL(self):
        try:self._paint()
        except Exception as exc:
            self.error=str(exc);self.ready=False
            self.timer.stop()
            print('Vitalux: 3D rendering failed:',self.error,flush=True)

    def _paint(self):
        if not hasattr(self,'gl'):return
        f=self.gl
        f.glClearColor(.95,.945,.93,1.);f.glClear(0x4000|0x0100)
        if not self.ready:return
        f.glEnable(0x0B71)
        projection=QMatrix4x4();projection.perspective(34,self.width()/max(1,self.height()),1.,2500.)
        distance=440*max(1.,1.15/(self.width()/max(1,self.height())))
        camera=QVector3D(self.pointer[0]*14,70+self.pointer[1]*10,distance)
        view=QMatrix4x4();view.lookAt(camera,QVector3D(0,-4,0),QVector3D(0,1,0))
        materials=((QVector3D(.91,.87,.79),.08,.22),
                   (QVector3D(.66,.74,.75),1.,.16),
                   (QVector3D(.58,.12,.045),.87,.24),
                   (QVector3D(.8,.77,.7),0.,.9))
        models=[]
        for index in range(4):
            model=QMatrix4x4()
            if index<3:
                model.rotate(-12,1,0,0);model.rotate(16+self.phase*3+self.pointer[0]*6,0,1,0)
                model.rotate(-16,0,0,1)
                if index==1:model.rotate(120,0,1,0);model.scale(1.025)
                elif index==2:model.rotate(25,1,0,0);model.rotate(-70,0,1,0);model.rotate(80+self.load*.15,0,0,1);model.scale(.9)
            models.append(model)
        light_matrix=self._shadow_pass(models)
        p=self.program;p.bind();p.setUniformValue(self.locations['viewProjection'],projection*view)
        f.glUniform3f(self.locations['cameraPosition'],camera.x(),camera.y(),camera.z())
        p.setUniformValue(self.locations['lightViewProjection'],light_matrix)
        f.glActiveTexture(0x84C0);f.glBindTexture(0x0DE1,self.shadow_target.texture())
        f.glUniform1i(self.locations['shadowMap'],0)
        f.glUniform1f(self.locations['time'],self.phase)
        for index,((vao,buffer,count),(color,metal,rough),model) in enumerate(zip(self.buffers,materials,models)):
            p.setUniformValue(self.locations['model'],model);p.setUniformValue(self.locations['normalMatrix'],model.normalMatrix())
            f.glUniform3f(self.locations['baseColor'],color.x(),color.y(),color.z())
            f.glUniform1f(self.locations['metalness'],metal)
            f.glUniform1f(self.locations['roughness'],rough);f.glUniform1f(self.locations['ground'],1. if index==3 else 0.)
            vao.bind();f.glDrawArrays(0x0004,0,count);vao.release()
        p.release()

    def _shadow_pass(self,models):
        f=self.gl
        light_view=QMatrix4x4();light_view.lookAt(QVector3D(-300,450,500),QVector3D(0,0,0),QVector3D(0,1,0))
        light_projection=QMatrix4x4();light_projection.ortho(-220.,220.,-220.,220.,.1,1600.)
        matrix=light_projection*light_view
        self.shadow_target.bind();f.glViewport(0,0,2048,2048)
        f.glClearColor(1.,1.,1.,1.);f.glClear(0x4000|0x0100)
        program=self.shadow_program;program.bind()
        program.setUniformValue(program.uniformLocation('viewProjection'),matrix)
        for (vao,buffer,count),model in zip(self.buffers[:3],models):
            program.setUniformValue(program.uniformLocation('model'),model)
            vao.bind();f.glDrawArrays(0x0004,0,count);vao.release()
        program.release()
        f.glBindFramebuffer(0x8D40,self.defaultFramebufferObject())
        ratio=self.devicePixelRatioF()
        f.glViewport(0,0,round(self.width()*ratio),round(self.height()*ratio))
        return matrix

    def cleanup(self):
        if not self.buffers:return
        self.makeCurrent()
        for vao,buffer,_ in self.buffers:buffer.destroy();vao.destroy()
        self.buffers=[]
        self.gl.glBindTexture(0x0DE1,0)
        self.shadow_target=None
        if self.shadow_program:self.shadow_program.removeAllShaders()
        if self.program:self.program.removeAllShaders()
        self.ready=False;self.doneCurrent()

    def advance(self):
        if not self.isVisible() or self.window().isMinimized() or not motion.enabled():
            self.timer.stop();return
        self.phase=(time.monotonic()-self.started)*(.15 if motion.level()=='reduced' else 1.)
        self.timer.setInterval(80 if motion.level()=='reduced' else 16)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if motion.enabled():self.timer.start()

    def hideEvent(self, event):
        self.timer.stop();super().hideEvent(event)

    def set_load(self, value):
        self.load=float(value or 0)
        if self.isVisible() and motion.enabled() and not self.timer.isActive():self.timer.start()
        self.update()


def probe():
    import os
    from PySide6.QtWidgets import QVBoxLayout
    app=QApplication([])
    host=QWidget(None,Qt.Tool|Qt.FramelessWindowHint)
    host.setAttribute(Qt.WA_DontShowOnScreen,True)
    view=SculptView(host)
    layout=QVBoxLayout(host);layout.addWidget(view)
    host.resize(660,440);host.show()
    def finish():
        image=view.grabFramebuffer()
        valid=view.ready and not image.isNull()
        if os.environ.get('VITALUX_SCULPT_CAPTURE') and valid:image.save(os.environ['VITALUX_SCULPT_CAPTURE'])
        if not valid:print(view.error,flush=True)
        host.close();app.exit(0 if valid else 3)
    QTimer.singleShot(1000,finish)
    QTimer.singleShot(8000,lambda:app.exit(4))
    return app.exec()


if __name__=='__main__':
    import sys
    sys.exit(probe())
