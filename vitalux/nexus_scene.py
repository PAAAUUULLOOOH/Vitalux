"""Native depth-layered Vitalux emblem, lit geometry and moving camera."""
from math import sin
from PySide6.QtGui import QColor,QMatrix4x4,QVector3D
from .sculpt_scene import SculptView
from . import nexus_geometry,theme
from .nexus import PALETTE


class NexusView(SculptView):
    ASSET_FOLDER='nexus'

    def build_geometry(self):
        self._upload(*nexus_geometry.rings())
        self._upload(*nexus_geometry.pulse())
        self._upload(*nexus_geometry.rings(111.,1.5,2.,((0,360),)))
        self._upload(*nexus_geometry.field())

    def _paint(self):
        if not hasattr(self,'gl'):return
        f=self.gl;f.glClearColor(.018,.035,.026,1.);f.glClear(0x4000|0x0100)
        if not self.ready:return
        f.glEnable(0x0B71)
        projection=QMatrix4x4();projection.perspective(40,self.width()/max(1,self.height()),1.,2500.)
        distance=590*max(1.,.95/(self.width()/max(1,self.height())))
        camera=QVector3D(self.pointer[0]*48,-self.pointer[1]*32,distance)
        view=QMatrix4x4();view.lookAt(camera,QVector3D(0,0,0),QVector3D(0,1,0))
        c=QColor(PALETTE['accent']);accent=QVector3D(c.redF(),c.greenF(),c.blueF())
        materials=((QVector3D(.22,.29,.20),.92,.22),(accent,.60,.24),
                   (accent,.82,.18),(QVector3D(.025,.055,.038),0.,.95))
        models=[]
        for index in range(4):
            model=QMatrix4x4()
            if index<3:
                model.translate(67,16+sin(self.phase*.18)*1.3,8 if index==1 else 0)
                model.rotate(-self.pointer[1]*4.5,1,0,0);model.rotate(self.pointer[0]*6.,0,1,0)
            models.append(model)
        light_matrix=self._shadow_pass(models)
        p=self.program;p.bind()
        p.setUniformValue(self.locations['viewProjection'],projection*view)
        p.setUniformValue(self.locations['lightViewProjection'],light_matrix)
        f.glUniform3f(self.locations['cameraPosition'],camera.x(),camera.y(),camera.z())
        f.glUniform1f(self.locations['time'],self.phase)
        f.glActiveTexture(0x84C0);f.glBindTexture(0x0DE1,self.shadow_target.texture())
        f.glUniform1i(self.locations['shadowMap'],0)
        for index,((vao,buffer,count),(color,metal,rough),model) in enumerate(zip(self.buffers,materials,models)):
            p.setUniformValue(self.locations['model'],model);p.setUniformValue(self.locations['normalMatrix'],model.normalMatrix())
            f.glUniform3f(self.locations['baseColor'],color.x(),color.y(),color.z())
            f.glUniform1f(self.locations['metalness'],metal);f.glUniform1f(self.locations['roughness'],rough)
            f.glUniform1f(self.locations['ground'],1. if index==3 else 0.)
            vao.bind();f.glDrawArrays(0x0004,0,count);vao.release()
        p.release()


def probe():
    import os
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout
    app=QApplication([]);theme.set_mode('nexus')
    host=QWidget(None,Qt.Tool|Qt.FramelessWindowHint);host.setAttribute(Qt.WA_DontShowOnScreen,True)
    view=NexusView(host);layout=QVBoxLayout(host);layout.addWidget(view)
    host.resize(900,600);host.show()
    def finish():
        image=view.grabFramebuffer();valid=view.ready and not image.isNull()
        if os.environ.get('VITALUX_NEXUS_CAPTURE') and valid:image.save(os.environ['VITALUX_NEXUS_CAPTURE'])
        if not valid:print(view.error,flush=True)
        view.cleanup();host.close();app.exit(0 if valid else 3)
    QTimer.singleShot(800,finish);QTimer.singleShot(8000,lambda:app.exit(4))
    return app.exec()


if __name__=='__main__':
    import sys
    sys.exit(probe())
