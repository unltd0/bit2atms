"""
Probe SmolVLA action conditioning — does swapping the instruction change the actions?

Feeds the same synthetic image and robot state to the policy with different instructions
and compares the resulting action chunks via cosine similarity.  Paraphrases of the
trained task should produce similar action sequences; unrelated instructions should diverge.

Usage:
    cd workspace/vla/ch04
    python probe_language.py
"""
import torch
import torch.nn.functional as F
from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK, OBS_STATE

CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"

# Pairs to compare against the anchor instruction: (label, instruction B)
ANCHOR = "pink lego brick into the transparent box"
PAIRS = [
    # ── same instruction as a self-similarity baseline ───────────────────
    ("same",        ANCHOR),
    # ── paraphrases of the trained task ──────────────────────────────────
    ("paraphrase",  "place the pink block in the box"),
    ("paraphrase",  "pick up the lego and put it in the container"),
    # ── unrelated instructions ────────────────────────────────────────────
    ("unrelated",   "wave hello"),
    ("unrelated",   "open the drawer"),
    ("unrelated",   "move the arm to the left"),
]

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"


def label_color(label):
    return {"same": GREEN, "paraphrase": YELLOW, "unrelated": RED}[label]


def similarity_bar(sim):
    filled = round(sim * 20)
    return "█" * filled + "░" * (20 - filled)


def get_action_vector(policy, tokenizer, cfg, instruction, img, device):
    """Run one forward pass and return the flattened, unit-normalised action chunk."""
    enc = tokenizer(
        instruction + "\n",
        padding="max_length",
        max_length=cfg.tokenizer_max_length,
        return_tensors="pt",
        truncation=True,
    )
    batch = {}
    for key in list(cfg.image_features.keys()):
        batch[key] = img.clone().to(device)
    batch[OBS_STATE] = torch.zeros(1, cfg.robot_state_feature.shape[0],
                                   dtype=torch.float32, device=device)
    batch[OBS_LANGUAGE_TOKENS]         = enc["input_ids"].to(device)
    # cast to bool — the policy's internal attention mask logic requires it
    batch[OBS_LANGUAGE_ATTENTION_MASK] = enc["attention_mask"].bool().to(device)

    policy.reset()
    with torch.no_grad():
        # predict_action_chunk returns (1, n_action_steps, action_dim)
        chunk = policy.predict_action_chunk(batch)
    flat = chunk.reshape(1, -1)
    return F.normalize(flat, dim=-1)


if __name__ == "__main__":
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading {CHECKPOINT} on {device} ...")
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()
    tokenizer = policy.model.vlm_with_expert.processor.tokenizer
    cfg = policy.config
    print("Policy ready.\n")

    # Synthetic image: gaussian noise with natural-image statistics
    torch.manual_seed(7)
    img = (torch.randn(1, 3, 480, 640) * 0.2 + 0.45).clamp(0, 1)

    # Cache action vectors so each instruction is only run once
    all_instrs = {ANCHOR} | {b for _, b in PAIRS}
    cache = {}
    for instr in all_instrs:
        print(f"  running: {instr[:70]}")
        cache[instr] = get_action_vector(policy, tokenizer, cfg, instr, img, device)
    print()

    print(f"  {'':11s}  {'anchor':38s}  {'comparison':38s}  {'sim':>4}  bar")
    print("  " + "-" * 106)
    for label, b in PAIRS:
        sim = (cache[ANCHOR] * cache[b]).sum().item()
        pct = int(sim * 100)
        color = label_color(label)
        bar   = similarity_bar(sim)
        print(f"  {color}[{label:10s}]{RESET}  {ANCHOR[:36]:36s}  {b[:36]:36s}  {pct:3d}%  {color}{bar}{RESET}")
