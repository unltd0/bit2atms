# Ch04 Changes — Session Log & Handoff Notes

## Commit History

### Committed (b0f4e72) — `ch4: rewrite around SO-101 MuJoCo interactive sim + reader UX fix`
- `courses/vla/ch04_vla/README.md` — Full rewrite (~665 lines, +446/-236)
- `reader.html` — Clickable filename copy on code blocks (+15 lines)
- `scripts/reset_workspace.sh` — Updated ch04 workspace file list

### Committed (0438e3b) — `ch4: add reference code folder + VLA framing rewrite`
- `courses/vla/ch04_vla/code/interact_so101.py` — Interactive SO-101 sim with manual tokenization (171 lines)
- `courses/vla/ch04_vla/code/probe_language.py` — Language probe script (123 lines)
- `courses/vla/ch04_vla/code/finetune_smolvla.sh` — Fine-tuning pipeline (20 lines)
- README: all code block paths fixed (`workspace/vla/ch04/` → `courses/vla/ch04_vla/code/`)
- README: VLA framing rewritten with clear Vision+Language→Action input/output tables
- README: removed filler about "no training, no collecting demos"
- `pi-changes-ch4.md` — This file (change log & handoff notes)

### Pending (not yet committed)
See "What needs to be done next" below.

---

## What Changed in Ch04 README

### Structural changes
| Before | After |
|--------|-------|
| 3 projects: A=Inference (gym_pusht), B=Probe, C=Fine-tune | 3 projects: A=Interactive Sim (SO-101 MuJoCo), B=Probe, C=Optional Fine-tune |
| Model: `lerobot/smolvla_base` on gym_pusht | Checkpoint: `lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace` on SO-101 MuJoCo sim |
| Single camera (`observation.image`) | Two cameras (`observation.images.up`, `observation.images.side`) |
| 2D actions (gym_pusht agent_pos) | 6-DOF joint targets (SO-101 qpos/ctrl) |
| Time: 3–4 days | Time: 2–3 days |

### New sections added
- **Honest domain gap callout** — explains why zero-shot won't complete the task in sim (real photos → synthetic renders)
- **Data flow diagram** — shows exact tensor shapes and transformations for each input/output
- **Camera setup explanation** — how free cameras approximate wrist-cam + overview-cam from training
- **Known instructions list** — `"pink lego brick into the transparent box"` is what the checkpoint was trained on
- `policy.reset()` importance explained in both "What to observe" and Common Mistakes

### Self-Check questions rewritten
All 5 questions now match the new SO-101 approach:
1. Arm barely moves → domain gap or missing reset()
2. Language probe shows no difference → vision dominates due to sim-to-real gap
3. Wrong camera key names → `ValueError: All image features are missing`
4. Why call `policy.reset()`? → action chunking buffer explanation
5. How many demos for new task? → 20–50, because pretraining handles the basics

### Common Mistakes rewritten
- Wrong camera key names (was: mismatched instruction at eval)
- Expecting zero-shot to complete task in sim (new)
- Forgetting `policy.reset()` between episodes (was: comparing at different conditions)
- Running fine-tuning on MPS/CPU (renamed from CUDA-only)
- Skipping `os.chdir` before loading XML (new — MuJoCo STL path resolution)

---

## API Discovery Journey (Why the Code Changed)

The session went through 5 iterations to figure out how to pass language instructions:

1. **Attempt 1:** `"task": [instruction]` → policy failed, wanted `observation.language.tokens`
2. **Attempt 2:** Used `make_pre_post_processors()` from LeRobot → Edinburgh checkpoint has no `policy_preprocessor.json`, failed
3. **Attempt 3:** Used smolvla_base as preprocessor source → worked partially but images came out as `(H,W,3)` numpy arrays instead of permuted tensors
4. **Attempt 4:** Tried to fix AddBatchDimensionProcessorStep → too complex, images still not properly converted
5. **Final (working):** Manual tokenization via `policy.model.vlm_with_expert.processor.tokenizer` — cleanest path

### The correct input format for this checkpoint:
```python
{
    "observation.images.up":              tensor(1, 3, 480, 640) float32 [0,1]
    "observation.images.side":            tensor(1, 3, 480, 640) float32 [0,1]
    "observation.state":                  tensor(1, 6)          float32   joint positions
    "observation.language.tokens":        tensor(1, N)          int64     tokenized instruction
    "observation.language.attention_mask":tensor(1, N)          bool      attention mask
}
```

### Tokenization (manual):
```python
tokenizer = policy.model.vlm_with_expert.processor.tokenizer
max_len   = policy.config.tokenizer_max_length
enc = tokenizer(instruction + "\n", padding="max_length", max_length=max_len, return_tensors="pt", truncation=True)
lang_tokens     = enc["input_ids"]
lang_mask       = enc["attention_mask"].bool()
```

---

## File Inventory After Changes

### Course reference code (committed with README in next step):
| Path | Purpose | Status |
|------|---------|--------|
| `courses/vla/ch04_vla/code/interact_so101.py` | Interactive SO-101 sim — type instruction, watch arm move | ✅ Correct version (manual tokenization) |
| `courses/vla/ch04_vla/code/probe_language.py` | Language conditioning probe — compare joint positions across instructions | ✅ Correct version (manual tokenization) |
| `courses/vla/ch04_vla/code/finetune_smolvla.sh` | Fine-tuning pipeline script | ✅ Created with content |

### Workspace files (gitignored, for student scratchpad):
| Path | Purpose | Status |
|------|---------|--------|
| `workspace/vla/ch04/interact_so101.py` | Copy of course reference | ✅ Synced from code/ |
| `workspace/vla/ch04/probe_language.py` | Copy of course reference | ✅ Synced from code/ |
| `workspace/vla/ch04/run_inference.py` | Old gym_pusht version (unused) | ⚠️ Leftover, can be cleaned up |
| `workspace/vla/ch04/eval_smolvla.py` | Empty placeholder | ⚠️ Can be removed |
| `workspace/vla/ch04/smolvla_finetune.py` | Empty placeholder | ⚠️ Can be removed |
| `workspace/vla/ch04/compare_zeroshot_finetuned.py` | Empty placeholder | ⚠️ Can be removed |

### Reader.html changes (committed):
- Added `.code-lang-btn` CSS class — clickable code block header with filename
- Added `copyFilename()` JS function — copies filename to clipboard on click, shows "Copied!" feedback for 1.2s
- Changed code-header from `<div>` to `<button>` for accessibility

---

## What Needs to Be Done Next

### All planned changes committed ✅
Two commits:
- `b0f4e72` — README rewrite + reader UX fix + reset script update
- `0438e3b` — code/ folder + path fixes + VLA framing rewrite

### Optional cleanup (not urgent)
The following workspace files are gitignored and don't affect the repo:
- `workspace/vla/ch04/run_inference.py` — old gym_pusht version, uses broken `"task"` API
- `workspace/vla/ch04/eval_smolvla.py` — empty placeholder
- `workspace/vla/ch04/smolvla_finetune.py` — empty placeholder
- `workspace/vla/ch04/compare_zeroshot_finetuned.py` — empty placeholder

Can be removed with:
```bash
rm workspace/vla/ch04/run_inference.py workspace/vla/ch04/eval_smolvla.py workspace/vla/ch04/smolvla_finetune.py workspace/vla/ch04/compare_zeroshot_finetuned.py
```

### Verify locally (optional)
```bash
python3 -m http.server 8080 &
# Open http://localhost:8080/reader.html#ch04
# Check all three code blocks render from courses/vla/ch04_vla/code/
# Check clickable filename copy works
```

---

## Key Decisions Made

1. **SO-101 MuJoCo over gym_pusht** — The Edinburgh SmolVLA checkpoint is fine-tuned on real SO-101 data with two cameras (up + side). Running it in a matching MuJoCo sim is more pedagogically honest than forcing it into gym_pusht.

2. **Domain gap is the feature, not a bug** — The chapter explicitly teaches that zero-shot won't work well because of the real→sim image distribution shift. This sets up Ch5 (real hardware) as the natural next step.

3. **Manual tokenization over LeRobot preprocessor** — The Edinburgh checkpoint doesn't ship with `policy_preprocessor.json`, and the smolvla_base preprocessor has shape mismatches. Manual tokenization via the VLM's tokenizer is simpler and more transparent for learners.

4. **Fine-tuning marked optional (Project C)** — Since the checkpoint was already trained on this exact dataset, fine-tuning is a pipeline exercise rather than a capability demonstration. Students can skip to Ch5 if they want.

---

## Files Modified Summary

| File | Change | Lines |
|------|--------|-------|
| `courses/vla/ch04_vla/README.md` | Full rewrite (SO-101 approach) | +446 / -236 |
| `reader.html` | Clickable filename copy UX | +15 / 0 |
| `scripts/reset_workspace.sh` | Updated ch04 file list | +1 / -1 |
| `courses/vla/ch04_vla/code/interact_so101.py` | New — interactive SO-101 sim | +171 lines |
| `courses/vla/ch04_vla/code/probe_language.py` | New — language probe script | +123 lines |
| `courses/vla/ch04_vla/code/finetune_smolvla.sh` | New — fine-tuning pipeline | +22 lines |
