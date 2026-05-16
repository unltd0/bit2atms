# Chapter 05 — Audio

**Time:** ~15 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

A single microphone is a device that converts sound (air pressure changes) into a varying electrical voltage. A microphone *array* is something qualitatively different — multiple microphones spaced at known distances. Software uses the tiny differences in when a sound reaches each microphone to compute *where* the sound is coming from. That trick — beamforming — is why Alexa works in a noisy kitchen and why a robot can follow voice commands from across a room.

Audio is a smaller part of robotics than cameras or LiDAR, but it's the natural interface for human-robot interaction and a useful sensor for anomaly detection in industrial settings.

---

## Single microphone

A stream of audio samples at 16, 44.1, or 48 kHz, 16–24 bits per sample, mono. Three flavors:

- **Electret** — classic analog capsule. Needs a bias resistor and an ADC on the host.
- **MEMS over I2S** — digital, three wires, common on Raspberry Pi-class boards.
- **USB** — plug-and-play on any host, no setup.

ROS2: `audio_common` → `audio_common_msgs/AudioData`. Outside ROS: PortAudio, PyAudio, GStreamer, FFmpeg, ALSA.

**Limitations.**
- **No direction info.** A single mic tells you what was said, not where it came from.
- **Acoustic environment matters more than the mic.** A $5 mic in a quiet room beats a $500 mic in a fan-noise lab.
- **Sample-rate matching.** If your speech recognizer wants 16 kHz and you capture at 48 kHz, resample.
- **Compression eats high frequencies.** Opus and PCM (uncompressed) are robot-friendly; MP3 isn't.

**Representative products.**

| Product | Tier | Interface | Output | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Electret + MAX9814 amp board](https://www.adafruit.com/product/1713) | Hobby | Analog (needs ADC) | Mono analog | ~$8 | Cheapest audio capture on any MCU |
| [ICS-43434 / SPH0645 I2S MEMS](https://www.adafruit.com/product/3421) | Hobby | I2S | Mono digital | ~$7 | Digital audio on Pi / ESP32, no analog noise |
| [Generic USB conference mic](https://www.amazon.com/) | Plug-and-play | USB Audio Class (UAC) | Mono digital | ~$20–$50 | Quickest path on a laptop / Jetson host |
| [Røde NT-USB Mini](https://rode.com/en/microphones/usb/nt-usb-mini) | Prosumer | USB | Studio-quality | ~$100 | Voice quality matters (assistant demos, recording) |

*Prices verified May 2026.*

---

## Microphone array

Multiple mics at known relative positions. Software uses the tiny differences in when a sound reaches each mic to compute *direction of arrival* (DoA) — an angle, 0–360°. *Beamforming* flips it around: shift each mic's signal in time and add them so signals from one direction reinforce each other while signals from other directions cancel out. The result is a virtual directional mic you can electronically steer toward whoever's talking.

Modern array chips (XMOS XVF3000 in the ReSpeaker) bundle DoA, beamforming, echo cancellation, and noise suppression. You don't write the algorithms; you read the output: a cleaned mono audio stream, a DoA angle, and a voice-activity (VAD) signal. Drivers: `respeaker_ros`.

**Limitations.**
- **Reverb breaks DoA.** Hard walls reflect sound; the array hears the reflection as coming from a different direction. Carpeted rooms behave much better than echoey halls.
- **Wind noise** overwhelms speech outdoors.
- **>5 m is hard.** Even good arrays struggle with conversational speech in noise past 5 m.
- **Multiple speakers** at once — still mostly unsolved.
- **Far-field mics are tuned for voice (300 Hz–8 kHz)** — not music fidelity.

**Representative products.**

![ReSpeaker Mic Array v2.0 — Seeed Studio](assets/products/seeed_respeaker_v2.png)

| Product | Tier | Mics | DoA range | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [ReSpeaker USB Mic Array v2.0](https://www.seeedstudio.com/ReSpeaker-Mic-Array-v3-0.html) | Hobby/prosumer | 4 | 360° | ~$65 | Default mic array for robots — XMOS DSP, ROS2 driver, well-supported |
| [ReSpeaker 4-Mic HAT (RPi)](https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/) | Hobby | 4 | 360° | ~$25 | Raspberry Pi HAT, less polished DSP than v2.0 |
| [Alexa-style 7-mic dev kits](https://developer.amazon.com/alexa/alexa-voice-service/dev-kits) | Prosumer | 7 | 360° | varies | Building Alexa-class voice frontends |
| [PUI Audio / Knowles digital arrays](https://www.knowles.com/) | OEM | 4–8 | 360° | varies | Volume integration, custom hardware |

*Prices verified May 2026.*

---

## What audio is used for in robotics

- **Voice commands** — wake-word + speech-to-text. ReSpeaker + Whisper / Vosk is a common stack.
- **Speaker localization** — robot turns to face whoever's talking. Built into mid-range mic arrays.
- **Acoustic event detection** — glass break, door slam, fall detection. Small ML models on audio features.
- **Machine fault diagnosis** — bearings make different sounds as they fail. Maintenance and QC stations listen for it.

---

## Going Deeper

- [`audio_common` package](https://github.com/ros-drivers/audio_common) — ROS audio capture / playback
- [Seeed Studio ReSpeaker wiki](https://wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0/) — full ReSpeaker reference
- [`respeaker_ros` driver](https://github.com/furushchev/respeaker_ros)
- [ODAS — Open embeddeD Audition System](https://github.com/introlab/odas) — open-source DoA + beamforming
- [PyAudio / sounddevice docs](https://python-sounddevice.readthedocs.io/) — quickest Python audio
- [OpenAI Whisper](https://github.com/openai/whisper) — speech-to-text that runs locally
- [Vosk](https://alphacephei.com/vosk/) — lighter offline STT, good for embedded
