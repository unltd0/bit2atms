# System Architecture

## High-level

```
+-------------------------------------------------------------------+
| LAPTOP (or mini-PC) — the "brain off the body"                    |
|   Ollama: Qwen 2.5 7B (local) OR Claude Haiku 4.5 (cloud)         |
|   Agent loop (Python + Pydantic AI, ReAct, max 6 steps)           |
|   World Model service (FastAPI + SQLite + Chroma)                 |
|   VLM gateway (Moondream2 / Qwen2.5-VL-3B)                        |
|   Streaming TTS (Piper) over fastrtc                              |
+----------------------- WiFi (ROS2 + HTTP) ------------------------+
                                  |
+---------------------------------+---------------------------------+
| ROBOT (Raspberry Pi 5 8GB, Ubuntu 24.04 + ROS2 Jazzy)             |
|   Nav2 + slam_toolbox + AMCL                                      |
|   LD19 / RPLidar C1 driver                                        |
|   Pi Camera 3 publisher                                           |
|   Wyoming satellite (openWakeWord + faster-whisper-tiny)          |
|   ReSpeaker XVF3800 USB driver (DOA topic)                        |
|   robot_localization EKF (wheel odom + IMU)                       |
|   opennav_docking + AprilTag detector                             |
|   Skill servers (ROS2 actions): go_to, describe_view, find...     |
|   Health telemetry publisher (battery, RSSI, /odom alive)         |
+--------------------------- USB / Serial --------------------------+
                                  |
+---------------------------------+---------------------------------+
| ESP32-S3 (Linorobot2 firmware via micro-ROS)                      |
|   Motor PID at 100 Hz                                             |
|   Encoder reading                                                 |
|   IMU sampling (MPU6050)                                          |
|   Battery voltage + current (INA226 over I2C)                     |
|   LED ring controller (mood, attention)                           |
+-------------------------------------------------------------------+
```

## Three planes, three contracts

### 1. Real-time control plane (ESP32 ↔ Pi)

micro-ROS over USB serial. ESP32 is the only thing that touches motors and reads encoders at 100 Hz. Pi never has to care about real-time. If Pi crashes, ESP32 stops the motors via watchdog.

**Contract:** ROS2 topics — `/cmd_vel` in, `/joint_states` + `/imu/data` + `/battery_state` out. Plus `/led_command` for visual mood.

### 2. Robot plane (Pi)

ROS2 Jazzy native. Nav2 owns navigation. slam_toolbox runs once to build the map; AMCL localizes in production. Wyoming satellite runs on-robot for sub-1s wake-word + STT. Skills are ROS2 actions exposed as MCP tools or HTTP endpoints to the agent.

**Contract:** ROS2 actions — each skill is an action with goal/feedback/result. `go_to(location_name)`, `describe_view()`, `find(object_description)`, `dock_now()`, `report(text)`.

### 3. Cognition plane (Laptop)

Off-robot for power and latency reasons. Agent loop in Python. Pydantic AI for tool schemas with runtime-injected enums (current `KNOWN_LOCATIONS` baked into `Literal` each turn). World model is a SQLite event log + Chroma vector store behind a small FastAPI service. VLM is behind a separate FastAPI gateway.

**Contract:** HTTP/REST between agent and world model + VLM. ROS2 action client between agent and skills.

## Why the three-plane split

- **Real-time control on ESP32**: a Pi can't do reliable motor PID under load. It will drop cycles when SLAM gets busy. ESP32 isolates it.
- **Robot brain on Pi**: it's where the sensors are. Nav2 wants to be close to LiDAR. STT wants to be close to mic.
- **Cognition off-robot**: LLM and VLM are too heavy and too power-hungry for a Pi 5. Putting them on the laptop also lets the user upgrade the brain without touching the robot.

This is the same split used by Hello Robot's Stretch (real-time on RT host, ROS on Pi, AI on laptop GPU).

## What runs where — full table

| Component | Where | Why |
|---|---|---|
| Motor PID, encoder, IMU read | ESP32-S3 | Real-time, 100 Hz |
| Nav2, slam_toolbox, AMCL | Pi 5 | Sensor proximity |
| Wake-word (openWakeWord) | Pi 5 | Continuous listening, low CPU |
| STT (faster-whisper-tiny) | Pi 5 | Low-latency for first response |
| TTS (Piper) | Pi 5 | Generates audio out the robot's speaker |
| ReSpeaker DOA | XVF3800 onboard DSP | DSP chip handles it |
| Camera publish | Pi 5 | Sensor proximity |
| Object detection (YOLO-nano, optional) | Pi 5 | Cheap event detection |
| LLM (Qwen 2.5 7B) | Laptop (Ollama) | Compute |
| VLM (Moondream2 / Qwen2.5-VL-3B) | Laptop (FastAPI) | Compute |
| Agent loop | Laptop | Co-located with LLM |
| World model (SQLite + Chroma + FastAPI) | Laptop | Persistent state |
| Cloud LLM fallback (Haiku 4.5) | Cloud | When local is offline or wrong |

## The agent loop, concretely

1. **User speaks.** ReSpeaker captures audio. openWakeWord on Pi fires.
2. **STT runs on-Pi** (faster-whisper-tiny.en, ~600ms first-token).
3. **DOA fires** in parallel. Robot pans head ~30° to face the speaker.
4. **Transcript + world snapshot + skill schemas** sent to laptop agent.
5. **Agent calls LLM** (Haiku cloud OR Qwen local).
6. **LLM emits tool calls.** Agent validates against runtime schema (current locations, current objects).
7. **First sentence of LLM output** streams to Piper TTS *while* tool calls execute.
8. **Tool calls dispatched** as ROS2 actions on the robot. Each returns a `SkillResult{status, reason, message, observations}`.
9. **Loop continues** until LLM emits final response or max_steps=6 hit.
10. **Final response** speaks via Piper, robot returns to idle pose, world model is updated with observations.

## Failure handling at each layer

| Layer | What can fail | Fallback |
|---|---|---|
| Wake-word | Misses or false-fires | Push-to-talk button on robot |
| STT | Wrong transcript | LLM asks for clarification |
| DOA | Wrong direction | Robot pans full 360° if confidence low |
| LLM (cloud) | Network down | Local Qwen via Ollama |
| LLM (local) | Hallucinated tool call | Pydantic validation rejects, returns to agent with error |
| Skill (e.g. Nav2) | Path blocked | Return SkillResult with reason='path_blocked', LLM decides retry/report |
| World model query | Object unknown | Return empty result with `available_objects`, LLM corrects |
| Battery low | Mid-task | State machine interrupts, returns to dock |
| Network down (full offline) | Everything | Rules-based intent classifier handles "go to X" basics |

## What we write vs what we use

**Use off-the-shelf:**
- ROS2 Jazzy
- Nav2, slam_toolbox, AMCL
- Linorobot2 firmware (ESP32 + micro-ROS)
- LD19 / RPLidar C1 ROS driver
- Wyoming protocol + wyoming-satellite + openWakeWord + faster-whisper + Piper
- ReSpeaker XVF3800 USB DOA (firmware on the chip)
- Ollama + Qwen 2.5 7B
- Pydantic AI (agent framework)
- opennav_docking + AprilTag detector
- robot_localization EKF
- SQLite + Chroma

**Write ourselves:**
- World model service (FastAPI, ~200 lines)
- Skill registry mapping ROS2 actions to Pydantic tool schemas
- Agent loop (ReAct with caps + streaming TTS handoff, ~300 lines)
- VLM gateway (FastAPI wrapper, ~50 lines)
- DOA → head-pan bridge (~50 lines)
- Battery management state machine (~150 lines, or use opennav_docking's)
- Health telemetry publisher (~30 lines)
- Rules-based intent classifier fallback (~50 lines)

Total custom code: ~1500 lines Python, no novel algorithms.
