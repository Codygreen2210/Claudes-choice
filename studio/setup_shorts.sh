#!/usr/bin/env bash
# One-shot setup for the Shorts studio.  Run from the repo root, on branch studio/animate:
#   bash studio/setup_shorts.sh
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); VT=${VT:-$HOME/vt}
mkdir -p "$VT/v" "$VT/kit"
echo "1/5 python packages"
pip install -q --break-system-packages numpy scipy pillow opencv-python-headless soundfile librosa pyloudnorm onnxruntime kokoro-onnx==0.6.1 trimesh scikit-image fast-simplification libigl 2>/dev/null \
  || pip install -q numpy scipy pillow opencv-python-headless soundfile librosa pyloudnorm onnxruntime kokoro-onnx==0.6.1 trimesh scikit-image fast-simplification libigl
echo "2/5 tools"
command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }
command -v gcc >/dev/null || { apt-get update -qq && apt-get install -y -qq gcc; }
echo "3/5 narrator voice models (~350 MB, once)"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$VT/v/$f" ] || curl -sSL -o "$VT/v/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
cp "$ROOT/studio/voice/beer_ref.wav" "$VT/v/beer_ref.wav"
echo "4/5 sound kit (instruments + sfx live on the studio/ponzi branch)"
if [ ! -d "$VT/kit/studio/sfx" ]; then
  git -C "$ROOT" fetch -q origin studio/ponzi
  git -C "$ROOT" archive FETCH_HEAD studio/instruments studio/sfx | tar -x -C "$VT/kit"
fi
echo "5/5 compile the renderer + 3D web deps"
(cd "$ROOT/studio/samples/web" && npm i -s)
cd "$ROOT/studio/toon" && python3 -c "import fast; print('renderer ok')"
echo "ready. VT=$VT  (voice models in $VT/v, sound kit in $VT/kit)"
