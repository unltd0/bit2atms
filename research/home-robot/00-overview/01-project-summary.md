# Project Summary

## One-line

A home robot that understands your space, hears who is talking and from where, observes continuously, answers grounded questions, and can be sent on errands.

## Form factor

Single mobile diff-drive robot, ~25 cm tall, ~600 g, ~0.4 m/s. Pan-tilt head with camera and 4-mic array. Stationary base optional with fixed "eye unit" observers in other rooms (stretch).

## Core capabilities

1. **Move autonomously** — diff-drive, ROS2 Nav2, LiDAR SLAM, obstacle avoidance
2. **Spatial awareness** — knows named locations (kitchen, couch, doorway, my desk)
3. **Hear humans** — wake-word, STT, TTS over 4-mic array
4. **Sound localization** — turns toward voice when called (±10-15°)
5. **Speaker identification** — knows who is talking (face-rec primary, voice secondary)
6. **Event-driven observation** — VLM fires on motion/sound/command, not continuous
7. **Question answering** — grounded in observations + spatial knowledge
8. **Errand execution** — "go check the kitchen" → navigate, observe, report

## What this is NOT

- A continuous always-recording surveillance camera
- A real Vision-Language-Action robot (no real-time closed-loop visual control)
- A manipulation robot (no arm, no gripper in v1)
- A multi-robot swarm (single mobile + optional 1-2 fixed observers)
- A platform you build "from scratch" — it composes existing pieces (ROS2, Wyoming, Ollama, slam_toolbox)

## Honest constraints

- **Budget:** ₹65-72k landed for the strong build. ₹38-42k compromised. ₹30k is not real.
- **Time:** 3 months of evening hours to a 70%-reliable robot. 1-week is a scaffold, not a product.
- **Reliability target:** 70% per-capability after 3 months, 90% after 6 months with auto-docking + telemetry.
- **Privacy:** event-driven recording, visible indicator LED, off-button, local-first inference where possible.

## Distinguishing bet

Most hobby home robots ship as either:
- A nav demo (TurtleBot 3 with no voice or LLM)
- A voice demo (Echo Dot replica with no body)
- A VLA toy (arm with a script)

This project bets on **the integration being the value** — the robot is genuinely useful because it composes spatial awareness, hearing, observation, and language into a single coherent agent. The hardware is not novel. The software is not novel. The composition is the work.

## Status

Research phase. No code, no parts ordered. Document everything before committing to a build.
