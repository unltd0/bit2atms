"""
Probe SmolVLA language conditioning — no sim, no domain gap.

Extracts the model's language embeddings for a set of instructions and
prints cosine similarity with a plain-English label so you can see at a
glance whether the model treats two instructions as similar or different.

Usage:
    python workspace/vla/ch04/probe_language.py
"""
import torch
import torch.nn.functional as F
from lerobot.policies.smolvla import SmolVLAPolicy

CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"

# Pairs to compare: (label, instruction A, instruction B)
PAIRS = [
    # ── same instruction as its own baseline ──────────────────────────────
    ("same",        "pink lego brick into the transparent box",
                    "pink lego brick into the transparent box"),
    # ── paraphrases of the trained task ──────────────────────────────────
    ("paraphrase",  "pink lego brick into the transparent box",
                    "place the pink block in the box"),
    ("paraphrase",  "pink lego brick into the transparent box",
                    "pick up the lego and put it in the container"),
    # ── unrelated instructions ────────────────────────────────────────────
    ("unrelated",   "pink lego brick into the transparent box",
                    "wave hello"),
    ("unrelated",   "pink lego brick into the transparent box",
                    "do nothing"),
    ("unrelated",   "pink lego brick into the transparent box",
                    "move left"),
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

def get_embedding(policy, tokenizer, max_len, instruction):
    enc = tokenizer(
        instruction + "\n",
        padding="max_length",
        max_length=max_len,
        return_tensors="pt",
        truncation=True,
    )
    with torch.no_grad():
        emb = policy.model.vlm_with_expert.embed_language_tokens(enc["input_ids"])
    mask = enc["attention_mask"].unsqueeze(-1).float()
    pooled = (emb * mask).sum(1) / mask.sum(1)
    return F.normalize(pooled, dim=-1)


if __name__ == "__main__":
    print(f"Loading {CHECKPOINT} ...")
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to("cpu")
    policy.eval()
    tokenizer = policy.model.vlm_with_expert.processor.tokenizer
    max_len   = policy.config.tokenizer_max_length
    print("Policy ready.\n")

    cache = {}
    for _, a, b in PAIRS:
        for instr in (a, b):
            if instr not in cache:
                cache[instr] = get_embedding(policy, tokenizer, max_len, instr)

    print(f"  {'':11s}  {'A':38s}  {'B':38s}  {'sim':>4}  bar")
    print("  " + "-" * 102)
    for label, a, b in PAIRS:
        sim = (cache[a] * cache[b]).sum().item()
        pct = int(sim * 100)
        color = label_color(label)
        bar   = similarity_bar(sim)
        print(f"  {color}[{label:10s}]{RESET}  {a[:36]:36s}  {b[:36]:36s}  {pct:3d}%  {color}{bar}{RESET}")
