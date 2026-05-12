# Software Stack

## Layers

```
+------------------------------------------------------------------+
| User                                                             |
+------------------------------------------------------------------+
| Voice (Wyoming)                                                  |
|  openWakeWord -> faster-whisper-tiny -> Piper                    |
+------------------------------------------------------------------+
| Agent (Pydantic AI, ReAct loop, max 6 steps)                     |
|  Skill schemas with runtime-injected enums                       |
|  LLM: Qwen 2.5 7B (Ollama) + Claude Haiku 4.5 (cloud fallback)   |
+------------------------------------------------------------------+
| World Model (FastAPI + SQLite + Chroma)                          |
|  events, locations, objects                                      |
+------------------------------------------------------------------+
| Skills (ROS2 actions)                                            |
|  go_to, describe_view, find, dock_now, ...                       |
+------------------------------------------------------------------+
| Robot capabilities                                               |
|  Nav2 + slam_toolbox + AMCL                                      |
|  opennav_docking + AprilTag                                      |
|  ReSpeaker XVF3800 DOA                                           |
|  VLM gateway (Moondream2 or Qwen2.5-VL-3B)                       |
+------------------------------------------------------------------+
| Middleware: ROS2 Jazzy (default DDS, not Zenoh yet)              |
+------------------------------------------------------------------+
| Hardware: Pi 5 (robot brain) + ESP32-S3 (Linorobot2 firmware)    |
+------------------------------------------------------------------+
```

## Per-layer choices

### Middleware: ROS2 Jazzy with default DDS

- **Pick:** Default Fast DDS or Cyclone DDS.
- **Why:** Every package we touch (Nav2, slam_toolbox, LD19 driver, robot_localization, opennav_docking, micro-ROS) is tested against DDS.
- **Not Zenoh yet:** rmw_zenoh is "RELEASED" in 2026 but multi-host on consumer WiFi still has rough edges. Keep as upgrade chapter for v2.
- **WiFi gotcha:** pin `ROS_DOMAIN_ID`, lock to one WiFi band, consider Cyclone over Fast DDS for better consumer-router multicast.

### SLAM/Nav: slam_toolbox + Nav2 + AMCL

- **Pick:** slam_toolbox async mode for mapping; AMCL in production.
- **Why:** Boring, well-trod, Steve Macenski-maintained.
- **Pi 5 tuning required:** `controller_frequency` 10 Hz (not 20), reduced AMCL particle count, EKF fusing wheel odom + IMU is non-optional.
- **Don't pick:** ORB-SLAM3 (no maintained ROS2 wrapper), Cartographer (in maintenance), RTAB-Map (wrong if LiDAR is primary).

### Robot base firmware: Linorobot2

- **Pick:** Linorobot2 ESP32 firmware via micro-ROS.
- **Why:** Actively maintained, ESP32 + Pi support, LD19 in their sensor matrix.
- **Saves:** ~3 weeks of motor PID + encoder + IMU firmware work.

### Voice: Wyoming protocol stack

- **Pick:** wyoming-satellite on robot + openWakeWord + faster-whisper (tiny.en or base.en) + Piper.
- **Why:** De-facto open standard. Maintained by Michael Hansen (ex-Rhasspy, now Home Assistant). All pieces work on Pi 5.
- **Latency on Pi 5:** wake ~200ms, faster-whisper-tiny.en first-token ~600-1200ms on 3s audio, Piper streams first chunk in ~200ms.
- **Don't pick:** Rhasspy 3 (dead), Coqui TTS (sunset), Mycroft 1 (defunct), eSpeak (terrible quality).
- **Maybe:** OVOS (Mycroft successor) is alive but heavier than Wyoming. Skip for v1.

### Sound DOA: ReSpeaker XVF3800 onboard DSP

- **Pick:** XVF3800 USB array. The chip does AEC, AGC, beamforming, DOA, VAD, dereverberation. Host CPU stays free.
- **Why:** USB plug-and-play, DOA exposed via serial/HID, no DSP code to write.
- **Fallback:** ReSpeaker Mic Array v3.0 (older XMOS, similar architecture) if XVF3800 unavailable.

### LLM: Qwen 2.5 7B (local) + Claude Haiku 4.5 (cloud fallback)

- **Pick local default:** Qwen 2.5 7B-Instruct via Ollama on laptop. ~88% single-turn tool-call validity per BFCL v3. ~600ms-1.2s TTFT on a decent laptop GPU.
- **Pick cloud fallback:** Claude Haiku 4.5. ~97% tool-call validity, ~700ms TTFT. ~₹0.10 per typical interaction.
- **Don't pick:** GPT-4 (overkill, expensive). Llama 3.2 3B (~70% tool-call, too unreliable). Phi-3.5 mini (~75%, similar). Local Qwen on Pi alone (~9s end-to-end, unusable).
- **Privacy framing:** Local Qwen for command parsing + cloud only for VLM/open-ended Q&A gives 90% of privacy benefit.

### VLM: Moondream2 (laptop) or Qwen2.5-VL-3B (if Jetson)

- **Pick:** Moondream2 (1.86B params) via FastAPI gateway on laptop. ~2-5s per call CPU, sub-second with GPU.
- **Why:** Small, capable enough for "describe what you see" / "find the X in this image."
- **Don't pick:** SmolVLM-256M/500M (too weak for find queries), LLaVA-NeXT (heavier), GPT-4V/Claude Vision (cost adds up at scale).
- **Pattern:** VLM behind FastAPI, NOT in a ROS2 node. Keeps heavy Python deps out of robot workspace.

### Agent framework: Pydantic AI

- **Pick:** Pydantic AI for tool definitions and agent loop.
- **Why:** Real tool-loop, real validators, multi-provider, no LangChain bloat.
- **Don't pick:** RAI (LangChain-coupled, opinionated, overkill for our 9 skills). ROSA (LangChain-coupled, designed for graph introspection not skill dispatch). Raw OpenAI tool-spec JSON (re-implement validation by hand). LangChain Agents (heavy).
- **Read for ideas:** RAI's Connector/Agent/Tool trichotomy, ROSA's prompt engineering wiki, Stretch AI's PickupExecutor hierarchy.

### MCP for robot tools

- **Use for:** chapter 1 demo (Claude Desktop talking to a sim robot via ros-mcp-server). Phone-app remote control of robot in v1.5.
- **Don't use for:** the production agent loop on the laptop. LLM and skills are in the same process; MCP adds 50-200ms IPC for nothing.

### Docking: opennav_docking + AprilTag

- **Pick:** opennav_docking ROS2 server with AprilTag (tag36h11) detector.
- **Why:** Built-in staging-pose → vision-control-loop → contact-detect state machine. AprilTag detection rate beats ArUco at distance/oblique angles.
- **Mechanical layer:** Y-funnel for caster + magnetic pogo pin contacts. Geometry does last 2cm.

### World model: SQLite + Chroma + FastAPI

- **Pick:** SQLite for events/locations/objects + Chroma for embeddings + FastAPI for query API.
- **Why:** No off-the-shelf "spatial + temporal + LLM-queryable" framework exists for hobby robots.
- **Don't pick:** Letta (chat agent memory, wrong shape), Mem0 (same), Hydra/Kimera (academic 3D scene graphs, too heavy).
- **Custom code:** ~200 lines.

### Frontend / dashboard (optional v1.5)

- **Pick:** Foxglove Studio for ROS2 visualization (built-in).
- **Optional:** small web dashboard for "what did robot see today" — Streamlit or simple Flask, ~100 lines.

## What we explicitly avoid

- **Frigate NVR integration** — Frigate is for cameras you already own. We have one on the robot.
- **Home Assistant as the brain** — wrong shape; HA's automation engine is rule-based, robots need behavior trees.
- **Building the robot as a HA integration** — couples uptime, wrong-shape automations, distracts.
- **End-to-end voice frameworks (LiveKit, Pipecat)** — built for WebRTC humans, not robots. fastrtc is the right pick.
- **Zenoh as primary middleware in v1** — keep DDS until DDS hurts.
- **Behavior tree generators (BTGenBot)** — overkill for 9 skills.

## What we actually build

| Component | Lines | Notes |
|---|---|---|
| World model service | ~200 | FastAPI + SQLite + Chroma |
| Agent loop | ~300 | Pydantic AI ReAct + caps + streaming TTS handoff |
| Skill schemas + dispatch | ~200 | Runtime-injected enums |
| VLM gateway | ~50 | FastAPI wrapper |
| DOA → head-pan bridge | ~50 | ROS2 node |
| Battery state machine | ~150 | If not using opennav_docking's |
| Health telemetry | ~30 | MQTT publisher |
| Rules-based intent fallback | ~50 | sentence-transformer + cosine |

Total custom code: **~1,500 lines Python + minimal C++ in micro-ROS firmware (mostly Linorobot2 stock)**. No novel algorithms.
