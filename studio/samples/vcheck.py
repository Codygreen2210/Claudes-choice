import sys, soundfile as sf, numpy as np
x,sr=sf.read(sys.argv[1]); m=x.mean(1); v,_=sf.read('voice.wav'); v=v[:len(m)]
for a,b in [(0.06,0.7),(0.7,1.3),(1.3,2.5),(2.5,3.5),(3.5,4.3)]:
    i,j=int(a*sr),int(b*sr); mm,vv=m[i:j],v[i:j]
    g=(mm@vv)/(vv@vv); r=mm-g*vv
    print(f'{a:.1f}-{b:.1f}  voice-over-bed {10*np.log10((g*g*(vv@vv))/(r@r)):5.1f} dB')
