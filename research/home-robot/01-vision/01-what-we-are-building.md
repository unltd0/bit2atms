# What We Are Building

## The user-facing description

A small mobile robot for the home that:

- Recognizes you by face when it sees you, by voice when it hears you
- Turns toward you when you call its name
- Drives to named places — "go to the kitchen," "go check the front door"
- Answers questions grounded in what it has observed — "where did I leave my keys," "did anyone come home this afternoon"
- Reports back from errands — "I went to the kitchen, the stove is off"
- Lives on a charging dock and returns to it when its battery is low
- Tells you when it can't do something instead of failing silently

## The interactions that matter

Three flagship use cases that, if all three work reliably, prove the platform.

### Use case 1 — "Where did I leave my X"

> *"Hey desky, where did I leave my keys?"*
>
> [Robot turns toward voice, ~1s]
>
> *"Last seen on the kitchen counter, 47 minutes ago. Want me to go check?"*
>
> *"Yes."*
>
> [Robot navigates to kitchen, captures view, runs VLM]
>
> *"They're still on the counter, next to the brown bag."*

**Coordination axis:** named-object memory + spatial query + multi-modal output.

### Use case 2 — "Tell me what happened"

> *"What happened while I was out?"*
>
> *"Two events I can summarize. The Amazon courier came at 2:14 PM and left a brown box by the door. Your housemate arrived at 5:30 and went to her room."*

**Coordination axis:** event-driven log + on-demand summarization + cross-time reasoning.

### Use case 3 — "Go check something"

> *"Go check if I left the stove on."*
>
> [Robot navigates to kitchen, points camera at stove, runs VLM]
>
> *"The stove looks off. All four knobs are pointing up."*
>
> [Returns to dock]

**Coordination axis:** intent → skill → navigation → perception → report.

## Why these three

Together they exercise every architectural surface:

|  | UC1 | UC2 | UC3 |
|---|---|---|---|
| Named objects | ✓ |  |  |
| Event log |  | ✓ | (logs result) |
| Spatial nav | ✓ |  | ✓ |
| VLM on-demand | ✓ | ✓ | ✓ |
| Voice in/out | ✓ | ✓ | ✓ |
| Multi-step plan |  |  | ✓ |

If all three work reliably for 30 days in a real home, the platform is real.

## Who is this for

**Persona:** A technically curious adult, age 30-50, lives in a 60-100 m² flat with 1-3 housemates, owns at least one Echo or Google Home, has been disappointed by the glassiness of smart-home tech, has some Linux comfort, will tinker with config but does not want to write motor PID code at week 6.

**Not for:** Roboticists who want a research-grade SLAM platform. Smart-home enthusiasts who want a Z-Wave bridge. Kids who want a toy. Companies who want a commercial product.

## The "this is good" test

After 30 days of running, the user keeps the robot on the dock and uses it weekly without prompting. The robot has not died in a corner. The user has not had to flash the SD card.

That is the bar. Anything less is a demo, not a product.

## What we are explicitly NOT building

- A continuous-recording camera. Privacy-by-architecture: event-driven only.
- A child-monitoring or elder-monitoring product. Different regulatory surface, different reliability requirements.
- A voice assistant. Voice is *one* input. The robot is the product.
- A platform with an SDK and third-party developers. Single-team build.
- A shippable consumer product. This is a personal project / open-source reference design.
- A research contribution. We compose known pieces; we don't invent.
