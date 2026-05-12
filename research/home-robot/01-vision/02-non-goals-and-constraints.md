# Non-Goals and Constraints

## Capabilities we deliberately are NOT building (and why)

| Capability | Why we're not doing it |
|---|---|
| Real-time VLA (closed-loop visual control) | Needs 16 GB+ GPU. Latency wrong by 10-100×. Not feasible at our budget. |
| Manipulation (arm, gripper) | Doubles BOM, introduces a class of failure modes (calibration, object slippage). Saves for v2. |
| Outdoor operation | Different sensors (GPS, sun-tolerant cameras), different mechanics. |
| Stairs / multi-floor | Adds a class of problems (cliff sensing, fall recovery) we don't want in v1. |
| Continuous video recording | Privacy + storage + thermal failure mode. Event-driven instead. |
| Acoustic-only speaker ID | 50% reliability in real homes. Replace with face-rec when robot is facing speaker. |
| Multi-room real-time tracking | Requires distributed observers; v1 is single mobile. |
| Picking up objects, even with magnet gripper | Hardest robotics problem in the world. Not in v1. |
| Conversation memory across days | LLM-as-a-friend territory. Useful but separate problem. |
| Federated multi-home presence | Out of scope. |

## Hard constraints

### Budget

- **Strong tier:** ₹65-72k landed (the honest "this works" build)
- **Compromised tier:** ₹38-42k (with documented capability cuts)
- **₹30k tier is not feasible** for the spec described. Don't pretend otherwise.

### Time

- **3 months of evening-hour work** to reach 70% reliability across all 8 capabilities
- **6 months** to reach 90% with auto-dock + telemetry
- "1 week" is a scaffold, not a robot

### Power and noise

- Operates on residential AC, never above 25 W draw
- Acoustic noise: motors + LiDAR audible but not disruptive (target <50 dB at 1 m)
- No active cooling fan if avoidable — passive cooler on Pi 5

### Privacy

- Event-driven observation only — no continuous recording
- Visible LED when actively observing (red), idle (blue), processing (yellow)
- Hardware off-switch on the robot
- All voice/face data stored locally, optional cloud LLM only for reasoning over already-extracted text events
- 24-hour rolling event log; older summarized to text, raw frames discarded
- Indian DPDPA 2023 considerations: housemate consent, no minor recording

### Reliability

- 30-day uptime without manual intervention as the bar
- Auto-dock and resume on low battery
- Hardware watchdog → autoreboot on hang
- High-endurance microSD card to survive power-loss events
- Mechanical bumper + cliff IR — must not wedge or fall

### Regulatory

- No commercial sale, no CE/FCC/BIS compliance burden in v1 (personal project)
- If this becomes a product, separate review needed

## Soft constraints

### Components must be available in India

If a part requires AliExpress import with 31% landed duty, it has to be replaceable by a stocked Indian alternative for course/replication purposes. Rule of thumb: any part whose import lead time exceeds 3 weeks is suspect.

### Software stack must be open and forkable

No proprietary middleware that locks the project. ROS2 Jazzy + open-source Wyoming + open-source Ollama. Cloud LLM (Claude Haiku 4.5) is acceptable as fallback but not required path.

### Skills must be composable

Every robot skill (`go_to`, `describe_view`, `find`, `report`) is a standalone callable. No skill assumes the existence of another. The agent loop composes them; skills don't compose each other.

## Out-of-scope decisions parked for v2

- Manipulation
- Multi-floor SLAM
- Distributed observer fleet
- Federated identity (knowing it's "Guru" across multiple homes)
- Active charging while moving (wireless rail)
- Gesture interaction
- Proactive notifications based on inferred intent ("you're heading out without your keys")
