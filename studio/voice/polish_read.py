"""Per-line Kokoro reads -> trimmed, line-end sag halved (WORLD), level ridden, joined with natural gaps."""
import json, sys, numpy as np, soundfile as sf, librosa, pyworld as pw
from scipy.ndimage import uniform_filter1d
from kokoro_onnx import Kokoro
SR=24000
out, lines_f, gaps_f = sys.argv[1], sys.argv[2], sys.argv[3]
lines=json.load(open(lines_f)); gaps=json.load(open(gaps_f))   # gap after each line (s)
k=Kokoro('/root/vt/v/kokoro-v1.0.onnx','/root/vt/v/voices-v1.0.bin')
st=0.8*k.get_voice_style('am_michael')+0.2*k.get_voice_style('am_fenrir')
def trim(y):
    env=uniform_filter1d(np.abs(y),240); thr=env.max()*10**(-38/20); idx=np.where(env>thr)[0]
    a=max(idx[0]-int(0.015*SR),0); b=min(idx[-1]+int(0.04*SR),len(y)); y=y[a:b].copy()
    n=int(0.008*SR); y[:n]*=np.linspace(0,1,n); y[-n:]*=np.linspace(1,0,n); return y
def lift(y, keep=0.45):
    x=y.astype(np.float64); f0,t=pw.harvest(x,SR,f0_floor=70,f0_ceil=320,frame_period=5.0)
    sp=pw.cheaptrick(x,f0,t,SR); ap=pw.d4c(x,f0,t,SR); v=f0>0
    if v.sum()<20: return y
    tv=t[v]; lf=np.log2(f0[v]); slope,icpt=np.polyfit(tv,lf,1)
    if slope<0:
        corr=-(1-keep)*slope*(t-tv[0]); corr=np.clip(corr,0,None); f0=np.where(v,f0*2**corr,0)
    z=pw.synthesize(f0,sp,ap,SR,5.0)[:len(y)]; return z.astype(np.float32)
def ride(y, amt=0.6):
    env=np.sqrt(uniform_filter1d(y**2,int(0.25*SR))+1e-9); ref=np.percentile(env[env>env.max()*0.1],70)
    g=(ref/np.maximum(env,ref*0.25))**amt; g=np.clip(g,0.7,2.2); g=uniform_filter1d(g,int(0.08*SR)); return y*g
parts=[]; voice=[]; t0=0.12
for i,l in enumerate(lines):
    y,_=k.create(l,voice=st,speed=1.12,lang='en-us'); y=trim(y); y=lift(y); y=ride(y)
    y=y/np.sqrt(np.mean(y**2))*0.08
    parts.append(np.zeros(int((t0 if i==0 else gaps[i-1])*SR))); parts.append(y)
    s=sum(len(p) for p in parts)/SR; voice.append([s-len(y)/SR,s])
parts.append(np.zeros(int(0.25*SR))); x=np.concatenate(parts); x=x/np.max(np.abs(x))*0.89
sf.write(out+'/narration.wav',x,SR); json.dump(voice,open(out+'/voice.json','w'))
print('total %.2f'%(len(x)/SR)); [print(i,'%.2f-%.2f'%tuple(v)) for i,v in enumerate(voice)]
