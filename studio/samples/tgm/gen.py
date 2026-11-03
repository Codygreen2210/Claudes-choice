# gen.py SHOT OUTDIR  -- photoreal still on CPU (RealVisXL V5 Lightning), 2 seeds
import sys, json, time, torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
shot, out = sys.argv[1], sys.argv[2]
S = json.load(open(sys.argv[3]))
p = S["shots"][shot].replace("WHO", S["who"]) + ", photorealistic, RAW photo, high detail, natural colors"
torch.set_num_threads(4)
repo = "SG161222/RealVisXL_V5.0_Lightning"
try: pipe = StableDiffusionXLPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16, variant="fp16")
except Exception as e: print("no fp16 variant", e); pipe = StableDiffusionXLPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, algorithm_type="sde-dpmsolver++", use_karras_sigmas=True)
for seed in [int(x) for x in (sys.argv[4].split(",") if len(sys.argv) > 4 else ["11", "23"])]:
    t = time.time()
    img = pipe(p, negative_prompt=S["neg"], width=768, height=1344, num_inference_steps=6, guidance_scale=1.6,
               generator=torch.Generator().manual_seed(seed)).images[0]
    img.save(f"{out}/{shot}_{seed}.png"); print(shot, seed, round(time.time() - t), "s", flush=True)
