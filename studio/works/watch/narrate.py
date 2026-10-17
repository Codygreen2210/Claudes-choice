# narrate.py: British male narration for the watch film, line by line, with timing for the picture.
import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M='/home/claude/work/kokoro'
k=Kokoro(M+'/kokoro-v1.0.onnx',M+'/voices-v1.0.bin')
LINES=[
("open","Inside this case, hundreds of tiny parts are keeping time. And not one of them runs on a battery.",0.9),
("spring","It all starts with a coiled ribbon of metal. The mainspring. Wind it tight, and it stores energy, like a drawn bow.",0.8),
("rotor","But nobody winds a Rolex. In nineteen thirty one, Rolex fitted a half moon weight, the Perpetual rotor. Every time your wrist moves, it swings, and winds the spring for you.",0.9),
("train","The spring wants to let go all at once. So a train of gears holds it back, passing the power along, wheel to wheel.",0.8),
("escape","At the end of the train sits the escapement. A little fork rocks back and forth, letting the escape wheel move just one tooth at a time.",0.5),
("tick","Tick. Tock.",1.0),
("balance","What sets the rhythm is the balance wheel, swinging on a spring as fine as a hair. Rolex makes theirs from a blue alloy called Parachrom, which magnets can't upset.",0.7),
("beat","It beats eight times every second. Twenty eight thousand, eight hundred times an hour.",0.9),
("hands","And each beat lets the gears creep forward, so the seconds hand sweeps in that smooth glide you'd spot across a room.",0.8),
("end","Fully wound, it will run for about three days on its own. No battery. Just a spring, a weight, and your wrist.",1.5)]
sr=24000; out=[np.zeros(int(0.4*sr))]; t=0.4; tim=[]
for name,txt,gap in LINES:
    a,sr=k.create(txt,voice='bm_george',speed=0.94,lang='en-gb')
    tim.append({'name':name,'t0':round(t,3),'t1':round(t+len(a)/sr,3),'text':txt})
    out+= [a, np.zeros(int(gap*sr))]; t+=len(a)/sr+gap
y=np.concatenate(out); sf.write('narration.wav',y,sr)
json.dump({'lines':tim,'total':round(t+1.0,3)},open('timing.json','w'),indent=1)
open('timing.js','w').write('window.TIMING='+json.dumps({'lines':tim,'total':round(t+1.0,3)}))
print(round(t,1),'s')
