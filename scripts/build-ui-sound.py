#!/usr/bin/env python3
"""Build Vitalux's original soft glass tap, without third-party samples."""
from pathlib import Path
import math,struct,wave

RATE=48000
DURATION=.115


def build(path):
    values=[]
    count=round(RATE*DURATION)
    for index in range(count):
        t=index/RATE
        attack=math.sin(min(1,t/.008)*math.pi/2)**2
        release=min(1,(DURATION-t)/.028)**2
        # A rounded fundamental and a short, quiet crystal overtone avoid the
        # former sustained high bell note during repeated navigation.
        tone=(math.sin(2*math.pi*440*t)*math.exp(-t/.029)
              +.22*math.sin(2*math.pi*660*t)*math.exp(-t/.018)
              +.035*math.sin(2*math.pi*880*t)*math.exp(-t/.012))
        values.append(round(4800*attack*release*tone))
    values[0]=values[-1]=0
    with wave.open(str(path),'wb') as output:
        output.setparams((1,2,RATE,0,'NONE','not compressed'))
        output.writeframes(struct.pack('<'+'h'*len(values),*values))


if __name__=='__main__':
    build(Path(__file__).resolve().parents[1]/'assets/audio/glass-click.wav')
