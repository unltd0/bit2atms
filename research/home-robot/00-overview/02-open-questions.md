# Open Questions

Decisions still on the table.

## Hardware

1. **Tier A (₹72k) vs Tier B (₹48k) vs Tier C (₹87k buy-base)?** Default is Tier A. Cost-vs-capability tradeoff documented; budget call to be made.

2. **Single mobile robot vs mobile + 1-2 fixed eye units?** Single is cheaper and simpler. Fixed observers add real value for "what happened in baby's room while I was out" but ~₹2k each + integration. Default: single mobile in v1; fixed observers in v1.5.

3. **RPLidar C1 (₹15k) vs LDRobot D500 (₹8-9k)?** C1 has better Slamtec ROS support and warranty. D500 saves ₹6k. Default: C1 unless tight budget.

4. **Pi 5 NVMe vs SD-only?** NVMe is dramatically more reliable but adds ₹4,800 + HAT complexity. Default: NVMe in Tier A, SD in Tier B with high-endurance card.

5. **3D-printed chassis vs acrylic kit?** Printed is bespoke and serviceable; acrylic is cheap and fragile. Default: hybrid — acrylic base, 3D-printed mounts and dock funnel.

## Software

6. **Local LLM (Qwen 2.5 7B) vs cloud (Haiku 4.5) as default?** Local for privacy + cost; cloud for reliability + latency. Default: cloud Haiku as primary, local Qwen as offline fallback. Reverse if user prioritizes privacy strictly.

7. **Wyoming voice satellite vs roll-your-own?** Wyoming is the de-facto standard. Default: Wyoming.

8. **Pydantic AI vs RAI vs ROSA?** Default: Pydantic AI (DIY ReAct), borrow from RAI/ROSA's source. Decision documented in agent-design.md.

9. **MCP for skill exposure?** Yes for chapter-1 demos and remote phone control. No for the production agent loop.

10. **Behavior trees as primary control vs LLM as primary?** Hybrid. Intent classifier + BT for fast path, LLM for ambiguous/multi-step.

## Operational

11. **Cloud LLM cost in production.** Haiku 4.5 at ~₹0.10/interaction × 50/day = ~₹150/month. Acceptable? Default: yes for v1, monitor.

12. **Privacy: cloud VLM vs local?** Moondream2 on laptop is genuinely usable, ~3-5s. Cloud VLM (Gemini 2.5 Flash) is sub-second. Default: local Moondream2 + cloud opt-in.

13. **Speaker ID: face-only or face+voice?** Face-rec is reliable; voice-only acoustic ID is not. Default: face-only with voice as soft signal ("known voice / unknown voice").

14. **Telemetry destination:** Home Assistant vs ntfy vs Telegram bot? Default: ntfy (simplest, push to phone).

15. **Map re-build cadence?** SLAM maps degrade with furniture movement. Default: re-map monthly or on user-flagged failure.

## Project

16. **One robot or two?** Build one to learn, iterate, then decide. Default: one.

17. **How long is the project?** Honest 3 months to 70%, 6 months to 90%. Default: 3-month milestone, decide on 6-month extension after.

18. **Open source the result?** Default: yes, GitHub repo with BOM, firmware, agent code. License TBD.

19. **Document the build as a course?** User originally said "forget the course, make it a project." Default: project first, document the build, decide on course based on what we learn.

20. **What does "v1 done" look like?** Default: 3 use cases (where-did-I-leave, what-happened, go-check) work for 30 days in user's home with auto-dock. v1 ships when this is true.

## Risks parked

- **Liability from food/medication/child interactions** — robot is not designed for these; document explicitly.
- **Battery swelling at month 6-8** — mitigated by quality BMS + balance leads + monitoring.
- **WiFi disruption breaking the agent** — mitigated by offline intent classifier fallback.
- **LLM prompt injection from observed text** — robot reads signs, packages, etc. Theoretically a vector. Mitigation: VLM output is treated as untrusted, never directly executed as commands.
- **Family member discomfort with robot in shared space** — household consent, off-button, opaque privacy story.
