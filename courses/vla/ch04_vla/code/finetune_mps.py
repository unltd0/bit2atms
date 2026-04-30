"""
Finetune SmolVLA action head on sim grip demos — Apple Silicon (MPS).

Freezes the VLM backbone (448M params), trains only the action head (1.64M).
300 steps takes ~10 min on MPS after the one-time warmup (see warmup_mps.py).

Usage:
    python finetune_mps.py

Prerequisites:
    1. Run collect_demos.py first to create workspace/vla/ch04/sim_grip_data/
    2. Run warmup_mps.py once (~60-90 min one-time cost, then cached)

Output: workspace/vla/ch04/smolvla_sim_grip_ft/
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "workspace", "ext", "lerobot", "src"))
import torch
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.smolvla import SmolVLAPolicy
from torch.utils.data import DataLoader
from torch.optim import AdamW

if not torch.backends.mps.is_available():
    print("MPS not available. Use finetune_smolvla.sh on a CUDA GPU instead.")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.realpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
DATA_DIR   = os.path.join(REPO_ROOT, "workspace", "vla", "ch04", "sim_grip_data")
OUT_DIR    = os.path.join(REPO_ROOT, "workspace", "vla", "ch04", "smolvla_sim_grip_ft")

CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"
TASK       = "grip the green box"
STEPS      = 300
LR         = 5e-4
BATCH      = 4
device     = torch.device("mps")

if not os.path.isdir(DATA_DIR):
    sys.exit(f"Dataset not found at {DATA_DIR}\nRun collect_demos.py first.")

print(f"Loading policy to MPS ...")
t0 = time.time()
policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
policy.model.vlm_with_expert.requires_grad_(False)
trainable = sum(p.numel() for p in policy.parameters() if p.requires_grad)
print(f"Trainable params: {trainable/1e6:.2f}M (action head only, VLM frozen)")
policy.train()

tokenizer = policy.model.vlm_with_expert.processor.tokenizer
max_len   = policy.config.tokenizer_max_length
enc = tokenizer(TASK + "\n", padding="max_length", max_length=max_len,
                return_tensors="pt", truncation=True)
lang_tokens = enc["input_ids"]
lang_mask   = enc["attention_mask"].bool()

print(f"Loading dataset from {DATA_DIR} ...")
delta_ts = {"action": [i / 30 for i in range(policy.config.n_action_steps)]}
dataset  = LeRobotDataset("local/sim_grip", root=DATA_DIR, delta_timestamps=delta_ts)
loader   = DataLoader(dataset, batch_size=BATCH, shuffle=True, num_workers=0, drop_last=True)
opt      = AdamW([p for p in policy.parameters() if p.requires_grad], lr=LR)

print(f"Finetuning {STEPS} steps on MPS ...")
it = iter(loader); loss_log = []; t_train = time.time()
for step in range(STEPS):
    try:   batch = next(it)
    except StopIteration: it = iter(loader); batch = next(it)

    B = batch["action"].shape[0]
    batch["observation.language.tokens"]         = lang_tokens.expand(B, -1).to(device)
    batch["observation.language.attention_mask"] = lang_mask.expand(B, -1).to(device)
    batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}

    t1 = time.time()
    opt.zero_grad()
    loss, _ = policy.forward(batch)
    loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in policy.parameters() if p.requires_grad], 1.0)
    opt.step()
    loss_log.append(loss.item())

    if step < 3 or step % 50 == 49:
        elapsed = time.time() - t_train
        eta = elapsed / (step + 1) * (STEPS - step - 1)
        print(f"  step {step+1}/{STEPS}  loss={loss.item():.4f}  "
              f"step_time={time.time()-t1:.1f}s  eta={eta/60:.1f}min")

policy.save_pretrained(OUT_DIR)
total = time.time() - t0
print(f"\nDone in {total/60:.1f}min.")
print(f"Loss: {sum(loss_log[:20])/20:.4f} → {sum(loss_log[-20:])/20:.4f}")
print(f"Checkpoint: {OUT_DIR}")
