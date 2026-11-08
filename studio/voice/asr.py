# rough offline speech-to-text of each narration line (pocketsphinx, pip install pocketsphinx): python3 asr.py DIR line [line...]  -- catches slurred or wrong words before sending
import sys, os, json, numpy as np, soundfile as sf, librosa
from pocketsphinx import Decoder, get_model_path
d = sys.argv[1]; mp = get_model_path()
dec = Decoder(hmm=os.path.join(mp, 'en-us', 'en-us'), dict=os.path.join(mp, 'en-us', 'cmudict-en-us.dict'), lm=os.path.join(mp, 'en-us', 'en-us.lm.bin'), loglevel='FATAL')
y, sr = sf.read(f'{d}/narration.wav'); y = y if y.ndim == 1 else y.mean(1); T = json.load(open(f'{d}/times.json'))
for i in map(int, sys.argv[2:]):
    a, b = T['voice'][i]; seg = y[int((a - 0.05) * sr):int((b + 0.05) * sr)]
    dec.start_utt(); dec.process_raw((librosa.resample(seg, orig_sr=sr, target_sr=16000) * 32767).astype(np.int16).tobytes(), full_utt=True); dec.end_utt()
    print(d.split('/')[-1], i, dec.hyp().hypstr if dec.hyp() else None)
