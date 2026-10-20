#!/usr/bin/env python3
"""Reproduce the original, softly damped Vitalux button tone (no samples)."""
from pathlib import Path
import math,struct,wave

RATE=48000
DURATION=.18


def build(path):
    values=[]
    count=round(RATE*DURATION)
    for index in range(count):
        t=index/RATE
        attack=math.sin(min(1,t/.012)*math.pi/2)**2
        release=min(1,(DURATION-t)/.035)**2
        envelope=attack*math.exp(-t/.040)*release
        tone=(math.sin(2*math.pi*740*t)+.16*math.sin(2*math.pi*1110*t)+.045*math.sin(2*math.pi*1480*t))
        values.append(round(6400*envelope*tone))
    values[0]=values[-1]=0
    with wave.open(str(path),'wb') as output:
        output.setparams((1,2,RATE,0,'NONE','not compressed'))
        output.writeframes(struct.pack('<'+'h'*len(values),*values))


if __name__=='__main__':
    build(Path(__file__).resolve().parents[1]/'assets/audio/glass-click.wav')
