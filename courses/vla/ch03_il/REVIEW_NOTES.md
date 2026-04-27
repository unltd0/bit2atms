# Ch03 Review Notes (2026-04-27)

## Large issues — not fixed yet

### Project B "collect targeted demos" is incomplete
The chapter tells learners to collect 20–30 targeted demos and retrain, but never explains *how*
to collect demos in gym_pusht. There's no teleoperation interface described anywhere.

**Options:**
1. Add a minimal mouse/keyboard demo collection script using gym_pusht's built-in teleop
2. Reframe Project B to only do the failure categorization step, and note that on a real arm
   (Ch7) you'd collect targeted demos — skip the retrain step entirely for this sim chapter

The "retrain" instruction at the end of Project B currently hangs in the air.

### Time estimate
- CUDA GPU: ~30 min (correct)
- Apple Silicon MPS: ~3–5 hours (now noted in Run callout)
- "1–2 days" header is achievable if learner has a GPU or is patient with MPS

