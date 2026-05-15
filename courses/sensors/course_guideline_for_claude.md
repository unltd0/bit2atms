# Course Guideline for Claude — Sensors

Use this when reviewing or generating content for the Sensors course.

---

## Course Goal

After this course, the learner can read a sensor datasheet, pick the right sensor for a robot they're designing, and recognize the failure modes that bite in the field. They are not an expert in any one sensor — they have a **map of the territory**.

This course is a **capability primer**, not a product catalog and not a textbook. It introduces *what a sensor does, what it emits, how to integrate it, and what to watch out for* — with links out for depth.

**Chapter arc:**

| Ch | Family |
|----|--------|
| 1 | Cameras — 2D, depth, plus event/thermal sidebars |
| 2 | LiDAR & Radar |
| 3 | IMU, GNSS & Wheel Odometry — the dead-reckoning trio |
| 4 | Proximity & Contact |
| 5 | Audio — mics and mic arrays |
| 6 | More sensors worth knowing — the discovery list |

**Reviewing a chapter:** ask whether a software engineer who has finished ROS2 ch01–ch02 could read it in 20 minutes and walk away knowing *what each sensor outputs, how to wire it in, and what will break it*. That's the right lens — not sensor-physics completeness.

---

## Target Audience

Python-literate software engineers who have completed the ROS2 course (or have equivalent ROS2 fluency). They know topics, msg types, TF, QoS. They want to understand the gear, not pass a robotics exam.

---

## Core Philosophy

**Structured > prose.** Tables and bullets beat paragraphs. If a paragraph is doing the work of a table, replace it with a table.

**Don't force fields.** Every block has the same field *order*, but if a field doesn't apply (no cloud offering, no trigger needed, no relevant non-ROS SDK), **omit it**. Never write "none" or "N/A" as a placeholder. Empty fields are scaffolding.

**Don't write scaffolding section titles.** Headings should name real content, not the role they play in the template. "Hook", "How it works in one paragraph", "Sidebar:" prefixes — all scaffolding. Just write the section with a heading that names what's in it.

**Capability, not catalog.** Three to six representative products per sensor — across hobby / prosumer / industrial tiers. Not exhaustive matrices. The point is to show the range, not list every SKU.

**Physics only where it pays off.** Only explain the underlying mechanism if it changes how you'd use or debug the sensor. *Why ToF struggles in sunlight* — yes. *Derive the Doppler equation* — no.

**Integration is first-class.** Every sensor block must answer: what physical interface, what ROS2 driver and msg type, and what non-ROS options exist.

**Limitations are first-class.** Every sensor block must list 3–6 concrete failure modes and gotchas. This is often the most useful field in the whole chapter.

**Link out for depth.** Vendor pages, datasheets, one or two seminal papers, one or two YouTube teardowns. Not exhaustive reading lists.

---

## Tone

- Direct, scannable, low-fluff
- Define each term the first time it appears
- Short sentences. No "In this section we will explore…"
- One hook per chapter — 1–2 sentences max, varied format (story, surprising number, broken assumption). After that, get to the structure.

---

## Chapter Structure

```
# Chapter N — Title

**Time:** ~20 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

## Hook

1–2 sentences. A real-world framing — what makes this sensor family interesting or
counter-intuitive. No more.

---

## <Sensor 1 name>

(see "Per-sensor block" below)

## <Sensor 2 name>

...

---

## How to choose

4–8 bullets. Quick decision guide: "if you need X, pick Y."

---

## Going Deeper

5–10 links. Vendor pages, datasheets, 1–2 YouTube teardowns (on their own line to
auto-embed), one paper if genuinely seminal.
```

No mandatory Self-Check, Try-It, Projects, or Common-Mistakes sections. Add only if they genuinely help. This course is a reference, not a project course.

---

## Per-sensor block (the core unit)

Each sensor in a chapter gets this exact block. Order matters — keep it consistent across the course.

```markdown
### <Sensor name>

**What it does.** 1–2 sentences.

**Senses.** The physical quantity (visible light, IR ToF, sound pressure,
angular rate, magnetic flux…).

**Input.** Power, trigger, config — short bullet list.

**Output.** Conceptual data shape (raw frame buffer, point cloud, samples).

**Integration.**
- **Physical interface:** USB / I2C / SPI / UART / Ethernet / CAN / PWM / MIPI-CSI
- **ROS2:** `<driver-package>` → `<msg-type>` (e.g., `realsense2_camera` → `sensor_msgs/Image`, `sensor_msgs/PointCloud2`)
- **Non-ROS:** vendor SDK / library, language bindings, platform support
- **Cloud / hosted:** *only include if the sensor genuinely has a cloud / hosted offering.* Omit otherwise — don't write "none" or filler.

**Limitations to watch out for.**
- Environmental failure mode (sunlight, rain, dust, EM interference…)
- Inherent error mode (drift, noise floor, latency, bias…)
- Range / resolution / FoV limits
- Things people get wrong

(Optional) **Why & how it works.** Only when the physics changes how you'd use the
sensor. 1–3 paragraphs max. Skip otherwise.

**Representative products.**

| Product | Tier | Interface | Headline spec | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Name](vendor-link) | Hobby | USB | … | $XX (2026-05) | … |

*Prices verified May 2026.*
```

---

## Product tables

- 3–6 rows per table. Cover hobby / prosumer / industrial tiers.
- Columns: photo (thumbnail), name (linked to vendor page), tier, interface, 1–2 headline specs, price USD (with verification date footnote), one-line "pick when".
- **Date-stamp pricing.** Every table ends with: *"Prices verified <month> <year>."*
- **Opinionated "pick when" column.** Not "general-purpose camera" — say *"pick when you want 1080p USB plug-and-play and don't care about latency"*.

---

## Images

**Always download — never hotlink.**

- Save to `courses/sensors/chXX/assets/products/<vendor>_<model>.jpg` for product photos
- Save to `courses/sensors/chXX/assets/<topic>.png` for physics diagrams
- Credit the source in alt text: `![Intel RealSense D435 — Intel product page](assets/products/intel_d435.jpg)`

Good sources:
- Manufacturer product pages (Intel, Ouster, Velodyne, Robotis, FLIR, u-blox, Bosch…)
- Wikimedia Commons (CC-licensed physics diagrams)
- Datasheet PDFs for internal block diagrams and signal traces

Avoid stock-photo sites and re-hosts of unclear provenance.

---

## YouTube embeds

A YouTube URL on its own line auto-embeds (reader feature). Use sparingly:

- 1–2 per chapter, max
- Prefer manufacturer demos, teardowns (Real Engineering, Branch Education, Skyentific), or famous failure-mode demos
- Don't embed long-form lecture videos — link them in *Going Deeper* instead

---

## Hardware tier labels (use exactly)

- `Laptop only` (default for this course)

This course is theory-first; chapters don't require physical hardware. If a chapter genuinely needs hardware (none do in v1), use the ROS2 course's labels.

---

## Exclude

- Deep math derivations (Kalman filter steps, projective geometry, Madgwick proof) — link to papers instead
- Vendor-specific driver setup walkthroughs — those belong in the ROS2 hardware chapter and they rot fast
- Code samples beyond a one-line msg type reference — this is not a coding course
- Exhaustive product catalogs — 3–6 representative options per sensor, no more
- Actuators (motors, encoders, servos, drivers) — separate future course
- Marketing fluff ("revolutionary new technology")
- Meta-commentary ("In this chapter we will…")
