import sys, time, numpy as np, cv2
import l1
from ovl import overlay
t0=time.time()
PAINT=l1.build_painting(); TEX=l1.build_tunnel(); print('build',time.time()-t0)
yy, xx = np.mgrid[0:l1.H, 0:l1.W].astype(np.float32)
l1.VIG=(1 - 0.35 * (((xx - l1.W / 2) / (l1.W * 0.75)) ** 2 + ((yy - l1.H / 2) / (l1.H * 0.75)) ** 2))[..., None]
ts=[float(x) for x in sys.argv[1:]]
st=l1.Cam(); outs=[]
for i in range(int(max(ts)*30)+1):
    t=i/30
    if t < l1.CUT:
        if any(abs(t-x)<1/60 for x in ts) or t>=0.76:
            a=time.time(); img=l1.frame_A(t,i,PAINT,st)
        else:
            l1.cam_A(t,st); continue
    else:
        if not any(abs(t-x)<1/60 for x in ts): continue
        a=time.time(); img=l1.frame_B(t,i,TEX,st)
    if any(abs(t-x)<1/60 for x in ts):
        print(t, 'sec/frame', round(time.time()-a,2))
        outs.append(cv2.resize(overlay(l1.finish(img*l1.VIG,t),t),(360,640)))
cv2.imwrite('still.png',cv2.cvtColor(np.hstack(outs),cv2.COLOR_RGB2BGR))
