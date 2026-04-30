"""
One-time Metal shader warmup for SmolVLA on Apple Silicon.

Run this once (~60-90 min). After completion, MPS finetuning takes ~10 min
for 300 steps. The compiled shaders cache permanently at:
  ~/Library/Caches/com.apple.metal/

The cache is device-specific — each Mac compiles its own shaders once.

Usage:
    cd workspace/vla/ch04
    python warmup_mps.py
"""
import sys, os, time
sys.path.insert(0, "../../ext/lerobot/src")

import torch

if not torch.backends.mps.is_available():
    print("MPS not available — run on Apple Silicon Mac")
    sys.exit(1)

device = torch.device("mps")
print(f"Metal shader warmup for SmolVLA")
print(f"Started: {time.strftime('%H:%M:%S')} — expect 60-90 min\n")

from lerobot.policies.smolvla import SmolVLAPolicy
from torch.optim import AdamW

t0 = time.time()
print("Loading policy to MPS (triggers shader compilation) ...")
policy = SmolVLAPolicy.from_pretrained(
    "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"
).to(device)
policy.model.vlm_with_expert.requires_grad_(False)
policy.train()
print(f"Policy on MPS: {(time.time()-t0)/60:.1f} min elapsed\n")

tokenizer = policy.model.vlm_with_expert.processor.tokenizer
max_len   = policy.config.tokenizer_max_length
enc = tokenizer("grip the green box\n", padding="max_length",
                max_length=max_len, return_tensors="pt", truncation=True)

B = 4
batch = {
    "observation.images.up":               torch.rand(B, 3, 480, 640, device=device),
    "observation.images.side":             torch.rand(B, 3, 480, 640, device=device),
    "observation.state":                   torch.rand(B, 6, device=device),
    "observation.language.tokens":         enc["input_ids"].expand(B, -1).to(device),
    "observation.language.attention_mask": enc["attention_mask"].bool().expand(B, -1).to(device),
    "action":                              torch.rand(B, policy.config.n_action_steps, 6, device=device),
}

opt = AdamW([p for p in policy.parameters() if p.requires_grad], lr=1e-4)

print("Running 3 training steps to finish shader compilation ...")
for step in range(3):
    t1 = time.time()
    opt.zero_grad()
    loss, _ = policy.forward(batch)
    loss.backward()
    opt.step()
    elapsed = time.time() - t1
    print(f"  Step {step+1}: {elapsed:.1f}s  loss={loss.item():.4f}")
    if step == 0:
        print(f"  (step 1 is slowest — most shaders compile here)")

total = time.time() - t0
print(f"\nWarmup complete in {total/60:.1f} min.")
print("Subsequent MPS runs will be fast. Cache at ~/Library/Caches/com.apple.metal/")
