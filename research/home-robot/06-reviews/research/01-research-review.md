# Research Review

**Reviewer profile:** Senior researcher in robotics + ML. Tracks the field across academia, industry labs, and open-source. Has published in CoRL/ICRA, has built field-deployed systems, knows the difference between what a paper claims and what works in someone's house.

**Read of:** the same project, with attention to where the technology trajectory is headed and whether the design choices age well.

---

## Summary

The architecture is competent for May 2026 and will be obsolete in three places by May 2027. None of the obsolescence is fatal — the design choices are reversible — but a project that's still being built when the trajectory has moved should know which parts to write loosely.

The core insight worth flagging: **this project is being built at exactly the wrong moment to commit to several technology choices**. End-to-end voice-action models, on-device VLA, and embodied LLM agents are all moving fast enough that the "right" answer in May 2026 is structurally different from the "right" answer in May 2027.

I'm not telling you to wait. I'm telling you which abstractions to keep loose so the rebuild in 18 months is a port, not a rewrite.

## What's solid for the next 3-5 years

**ROS2 + Nav2 + slam_toolbox.** This stack will not be replaced. It's getting better (Zenoh RMW is real, Iron + Jazzy + Kilted convergence is healthy), but the abstractions are stable. Build on it without hesitation.

**Diff-drive base + 2D LiDAR for indoor nav.** This is solved well below the point where research moves the needle for hobbyist-scale robots. NVIDIA nvblox + cuVSLAM are state-of-the-art and don't matter for a Pi-class robot.

**ESP32-S3 + micro-ROS for real-time control.** Will be replaced eventually by something with more bandwidth (RP2350, ESP32-P4) but the architectural pattern (real-time MCU + ROS Pi) is permanent.

**Wyoming protocol + openWakeWord + Whisper + Piper.** The "voice satellite + brain" decoupling is the right shape. Wyoming itself may evolve but the pattern is durable.

## What's wobbly — choices made at the wrong inflection point

### 1. Tool-calling LLM as orchestrator is mid-cycle technology

You've designed around `LLM emits tool calls → skills execute → result returns to LLM → repeats`. This is the 2024-2025 pattern. By late 2026, several alternatives are landing:

- **Direct action models** that take observations + language and emit actions without going through a discrete skill registry. Pi-Zero, OpenVLA-OFT, π0 successors. These are RT-2 descendants designed for embodied agents.
- **Streaming agent loops** where the LLM doesn't emit discrete tool calls but a continuous trajectory of intent that gets executed in parallel.
- **Reasoning-trained models** (o1/o3 lineage, DeepSeek-R1 variants) where the orchestration logic is *in the chain of thought* rather than in your loop code.

Your ReAct-with-caps loop is fine for May 2026. By Q2 2027 it will look ancient. The skill registry abstraction is durable; the loop wrapper around it is not.

**Recommendation:** keep the skill registry as a clean ROS2-action interface. Decouple it from the agent loop entirely. The agent loop should be replaceable in <500 lines. You've roughly done this; explicit testing of "swap Pydantic AI for direct-action-model" as an integration point would be smart.

### 2. The "VLM as on-demand describe()" call is being replaced by always-on world models

Your design treats the VLM as an oracle the LLM calls when it needs to know what's in front of the robot. The trajectory is toward **continuous spatial-semantic memory** — the robot maintains a 3D scene graph that's queryable in O(1), and the VLM updates it asynchronously rather than being called per-question.

MIT-SPARK Hydra (open-set semantics, 2025) and Khronos (3D scene graphs over time, 2025) are the academic version of this. ConceptFusion, ConceptGraphs, OK-Robot are nearer-deployment versions. Within 12-18 months, the right architecture for "where did I leave my keys" is **query an always-up-to-date scene graph**, not **VLM-on-demand on the latest frame**.

This matters because your world model schema (locations table + objects table + events table + Chroma embeddings) is a flat key-value approximation of what's becoming a structured spatial graph. The graph is more powerful (geometric and semantic relations), more efficient (no full-frame VLM call), and is where research is heading.

**Recommendation:** start with your simpler schema; it works for v1. But abstract the world model behind a query API (which you've done — the FastAPI endpoints) so swapping the SQLite implementation for a 3D scene graph is local. Don't bake "objects are flat rows" into the rest of the architecture.

### 3. The cloud LLM choice will be obsolete in 12 months

Claude Haiku 4.5 today. By mid-2026 there will be a cheaper/faster/smarter model. By 2027, a Haiku-class model will run on a $300 mini-PC at full speed. The local/cloud split you've designed is the right hedge for now, but the assumption "cloud is faster, local is fallback" inverts within 24 months. You're already at the edge — Qwen 2.5 7B on a decent laptop is closing on Haiku 4.5 quality at 5× the latency.

**Recommendation:** code the agent loop to be provider-agnostic from day one (Pydantic AI gives you this). Make it routine to swap models. Re-evaluate quarterly which one is the *primary* path.

### 4. Speech recognition is a research topic that's about to become solved

You've picked faster-whisper-tiny on Pi for low latency, accepted ~600-1200ms first-token. By Q4 2026, on-device streaming ASR with sub-200ms first-token is realistic on Pi-class hardware (Sherpa-ONNX, the Wav2Vec2 lineage, NVIDIA's Riva-light variants for ARM). The voice latency budget shrinks 3-5x in the next year.

This is good news for you — it means the UX gets better without you doing anything. But it also means **the voice subsystem you ship now will feel laggy compared to the voice subsystem of late-2026 robots**. Plan to update.

### 5. The "single mobile robot" vs "distributed observers" decision will look different

Right now you've cut to single mobile because of cost (~₹2k per fixed observer adds up). The trajectory is toward **ESP32-class observer nodes that are actually free** — within 24 months, $5 ESP32-S3 + camera modules with on-device person detection (using small-VLM distilled models) will be cheap enough that "put 3 of these around the home" is the default for any home robot system.

Your architecture supports adding observers (the ROS2 message bus + world model schema accepts external observation events). Make sure that's true in code, not just in the doc.

## What's missing that the field thinks matters

### A. Memory beyond the event log

Episodic memory of *interactions* — "you asked me last week to remember the keys are usually on the hook" — is becoming the differentiator between robots that feel like products and robots that feel like demos. Letta, MemGPT, Mem0 are doing the chat-agent version. The robot version doesn't exist cleanly yet but it's coming.

Your world model has events. It doesn't have *promises made* or *user preferences inferred* or *routines learned*. That's a layer above what you've designed.

**Recommendation:** plan for a "user model" alongside the world model. v1 doesn't need it; v2 should.

### B. Multi-modal grounding for the LLM

When your LLM gets the world snapshot, it's text. *"keys: sofa, living_room (last seen 14:28)"*. The LLM doesn't see the *image* of the keys, the relative position to the sofa, the lighting. Multi-modal LLMs that can ingest the snapshot + an image + a query simultaneously are landing fast (Gemini 2.5 Flash, Qwen2.5-VL-72B).

Your architecture treats vision and language as separate tracks. The trajectory is toward integration. Worth flagging.

### C. Continuous learning vs static skills

Your skill registry is fixed at design time. Real product robots will need to *acquire skills* — "next time you go to the kitchen, also check whether the dishwasher is running." This is the trajectory toward in-context-learned skills.

For v1: don't build this. For v2: think about it.

### D. The simulation-to-real story

You've designed for real hardware, no sim. Most production-quality robotics today builds in sim first (Isaac Sim, Gazebo, MuJoCo) and validates the agent loop, the navigation, the failure handling in sim before touching hardware. Your project will skip that and pay for it in week-1-of-real-hardware debugging.

Hello Robot's stretch_ai, NVIDIA's Isaac samples, Pollen's Reachy Mini all ship with sim environments. Yours doesn't.

**Recommendation:** build a Gazebo or Isaac Sim simulation of the robot in parallel with the real one. The agent loop, the world model, the skill dispatch all should be testable in sim before being tested on hardware. This is one of the biggest reliability multipliers and the doc doesn't mention it.

## What I'd publish as a paper from this

Mostly nothing. The architecture is good engineering, not a research contribution. There's one possible angle:

**"Composing existing pieces: a working open-source home robot at <$1k BOM."** Not a research paper, but a workshop paper at IROS or CoRL Embodied AI Workshop. The contribution is the integration story + a public repo + a 6-month field deployment writeup. People care about reproducible references; "here's the BOM, here's the code, here's what broke" is genuinely useful.

If you actually field-deploy and instrument it well, the failure-mode taxonomy (the 30-day list, the demo-to-daily gap) could be a reproducibility paper. There's almost nothing in the literature that systematically reports "here's what kills hobby home robots in week 4."

## My recommendation, technical

Build it. The choices are sound for May 2026. Keep three abstractions explicitly loose:

1. **Agent loop** — should be replaceable in <500 lines. Don't bake LangChain/Pydantic-AI into other layers.
2. **World model storage** — should be replaceable behind the FastAPI. Don't let SQLite-isms leak.
3. **Voice subsystem** — should be a Wyoming-protocol satellite that can be entirely replaced. You've done this.

Plan for a v2 in 18 months that swaps:

- Direct-action model in for ReAct loop (or alongside)
- 3D scene graph in for flat object table
- On-device VLM in for VLM-on-laptop
- Continuous learning skills in for fixed registry

The v1 you've designed is the right v1. Just don't let it lock you into being the wrong v2.

## Score

Engineering soundness for May 2026: 8.5/10
Trajectory awareness: 5/10 — sound choices, but the doc reads as if technology is static
Forward-compatibility of architecture: 7/10 — abstractions are mostly clean

The biggest single fix: write a `99-trajectory.md` that documents which choices are time-locked and which are durable. Saves the v2 team a lot of archaeology.
