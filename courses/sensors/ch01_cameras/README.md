# Chapter 01 — Cameras: 2D & Depth

**Time:** ~30 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

Cameras are the most-used sensor in robotics by an enormous margin — cheap, dense, and the only sensor that gives you semantic information (this is a person, that is a car). The catch is that every camera also needs compute behind it to extract anything useful.

Depth cameras (stereo, time-of-flight, structured light) are just regular cameras with one extra trick to recover distance per pixel.

Two terms used throughout:
- **SLAM** — Simultaneous Localization and Mapping: figuring out where you are while building a map.
- **VLA** — Vision-Language-Action model: a neural network that takes images and text and outputs robot actions.

---

## 2D camera (RGB / mono)

You know what a camera does. ROS2 publishes each frame as `sensor_msgs/Image` plus a `sensor_msgs/CameraInfo` (calibration numbers). Drivers: `v4l2_camera` or `usb_cam` for any USB webcam; `image_pipeline` handles rectification.

Two things actually worth knowing:

- **Rolling vs global shutter.** Most cheap cameras read pixels row-by-row (rolling shutter), so fast motion produces slanted images. Machine-vision cameras read every pixel at once (global shutter) — no motion artifacts, but 3–10× the price.
- **Calibration is mandatory** for any geometric use (stereo, fusion with LiDAR, projecting points into the image). Point the camera at a checkerboard, run `camera_calibration`, and the driver publishes the resulting numbers in `CameraInfo`.

![Pinhole camera model — Wikimedia Commons (CC BY-SA 3.0)](assets/pinhole_camera.svg)

**Limitations.**
- **Motion blur and rolling shutter** — see above. Pay for global shutter if you need accuracy on a moving robot.
- **Dynamic range.** A camera sees roughly a 1000:1 range of brightnesses at once; the real world spans 100,000:1+. Walking from a sunlit window to a shaded room blows out one or the other.
- **White balance.** Auto white balance shifts colors as lighting changes — bad news for ML models trained on one lighting condition.
- **Lens distortion.** Wide-angle lenses curve straight lines; calibration corrects it.
- **Compression artifacts.** USB webcams compress to MJPEG. ML pipelines trained on raw images degrade on compressed ones.
- **Bandwidth.** 1080p × 60 fps × 3 channels is ~370 MB/s raw. USB 3.0 or compression is the only way to ship it.

**Representative products.**

| Product | Tier | Resolution | Shutter | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) | Hobby | 12 MP | Rolling | ~$25 | MIPI-CSI on a Pi-class SBC; cheap and small |
| [Logitech C920 / C922](https://www.logitech.com/en-us/products/webcams/c920-pro-hd-webcam.html) | Hobby | 1080p / 30 fps | Rolling | ~$70 | Plug-and-play USB; great default webcam |
| [Arducam global-shutter](https://www.arducam.com/) | Prosumer | 1–5 MP | Global | ~$30–$80 | Fast motion, no rolling-shutter artifacts, hobbyist budget |
| [FLIR Blackfly S](https://www.flir.com/products/blackfly-s-usb3/) | Industrial | 0.4–24 MP | Global or rolling | ~$400–$1,500 | Repeatable image acquisition with hardware triggers |
| [Basler ace 2](https://www.baslerweb.com/) | Industrial | 0.4–24 MP | Both options | ~$500–$2,500 | Production-line machine vision |

*Prices verified May 2026 from manufacturer and distributor pages.*

---

## Depth camera: stereo

Two cameras a few cm apart. Software finds the same point in both images and computes depth from how far apart it appears — closer objects shift more between the two views.

![Stereo disparity → depth — Wikimedia Commons (CC BY 4.0)](assets/stereo_disparity.svg)

Outputs an RGB image, a depth image (`sensor_msgs/Image`), and a point cloud (`sensor_msgs/PointCloud2`). Drivers: `realsense2_camera`, `zed-ros2-wrapper`, `depthai-ros`.

**Limitations.**
- **Blank surfaces fail.** Stereo matching needs visual texture; a plain white wall has nothing to match — depth image full of holes.
- **Reflective / transparent surfaces** (glass, mirrors, polished metal) break stereo matching.
- **Compute cost.** Stereo matching needs a GPU or on-device DSP. Cheap stereo without compute is slow.
- **Sunlight is fine** — a real advantage over IR-projector depth cameras.

---

## Depth camera: time-of-flight (ToF)

Fires its own infrared light at the scene and times the return per pixel. Outputs the same depth image + point cloud as stereo, but without the "needs texture" problem — plain walls work fine.

**Limitations.**
- **Outdoor performance dies.** Direct sunlight floods the IR sensor; indoor only.
- **Dark / matte surfaces** (matte black, fur) absorb the IR pulse — no return, no depth.
- **Mirrors / glass** return the depth of whatever's behind them. Confusing.
- **Multi-path interference.** IR bouncing in corners produces systematically wrong depths.
- **Short product lifecycles** in this space. Microsoft discontinued Azure Kinect in 2023; Intel discontinued the L515. Active vendors: Orbbec, Pico Zense.

---

## Depth camera: structured light

Projects a known infrared pattern (dots or stripes) onto the scene; an IR camera reads how the pattern deforms; the deformation gives depth. Same indoor-only failure mode as ToF, plus a short range (~2 m for good accuracy). Mostly historical — the original Kinect v1 made it famous; stereo and ToF have displaced it. Worth knowing when you see one, not worth picking new.

---

## Event cameras

Instead of returning frames, each pixel independently fires an event whenever it gets brighter or darker. No motion blur, microsecond timing, ~1000× the dynamic range of a frame camera, and almost no power use when the scene is still.

The output is a stream of `(x, y, time, brighter/darker)` events — millions per second. Most code expects frames, so vendor SDKs reconstruct frame-like images from the event stream.

Niche today (toolchain is young, ML training data scarce), but the right answer for high-speed drones, vibration analysis, and very-low-light work. Products: [Prophesee EVK4](https://www.prophesee.ai/event-camera-evk4/) (~$3,000), [Inivation DAVIS346](https://inivation.com/) (~$5,000).

---

## Thermal cameras

Reads heat as an image — each pixel gives the temperature of what it sees. Sees through smoke and total darkness; detects living things against background; spots overheating equipment from a distance.

**Limitations.**
- Low resolution (160×120 to 640×512). Don't expect to read text.
- Glass and many plastics are opaque in thermal IR. Can't see through windows.
- Starts at ~$300; nice ones cost thousands.
- Higher-resolution units are export-controlled (ITAR — US arms regulations) and can't be freely shipped to all countries.

**Products:** [FLIR Lepton 3.5](https://www.flir.com/products/lepton/) (~$250 module), [FLIR Boson+](https://www.flir.com/products/boson-plus/) (~$2,500), [Seek Thermal](https://www.thermal.com/) (~$200–$500 USB). Pick when: search & rescue, building inspection, agricultural monitoring, security.

---

## Depth camera comparison

| Product | Tech | Range | RGB | IMU | Price (USD) | Pick when |
|---|---|---|---|---|---|---|
| [Intel RealSense D435 / D435i](https://www.realsenseai.com/products/stereo-depth-camera-d435/) | Stereo + IR projector | 0.3–3 m (best), up to 10 m | Yes | D435i only | ~$300 / $400 | Default depth camera; huge ROS2 community |
| [Intel RealSense D455 / D456](https://store.intelrealsense.com/buy-intel-realsense-depth-camera-d455.html) | Stereo + IR projector | 0.6–6 m | Yes | Yes | ~$400 / $600 (D456 IP65) | Longer range, outdoor-friendly (D456 is dust+water rated) |
| [Stereolabs ZED 2i](https://www.stereolabs.com/store/products/zed-2i) | Passive stereo | 0.3–20 m | Yes | Yes | ~$500 | Outdoor work, long-range stereo with onboard SLAM |
| [Luxonis OAK-D Lite](https://shop.luxonis.com/products/oak-d-lite-1) | Stereo + on-device AI | 0.2–8 m | Yes | No | ~$130 | Cheap depth + on-device neural inference (object detection without a host GPU) |
| [Microsoft Azure Kinect](https://azure.microsoft.com/en-us/products/kinect-dk/) | ToF + RGB | 0.5–5 m | Yes | Yes | discontinued by Microsoft in 2023; used units ~$300 | Indoor body-tracking research; compatible with widely-cited public datasets |
| [Orbbec Femto / Gemini](https://www.orbbec.com/) | ToF or stereo | 0.2–5 m | Yes | Some | ~$200–$500 | Indoor robots; ToF without the Kinect lock-in |

*Prices verified May 2026 from manufacturer and distributor pages.*

![Intel RealSense D435 — RealSense](assets/products/intel_realsense_d435.png) ![Stereolabs ZED 2i — Stereolabs](assets/products/stereolabs_zed2i.png) ![Luxonis OAK-D Lite — Luxonis](assets/products/luxonis_oakd_lite.webp)

---

## Depth camera vs [LiDAR](../ch02_lidar_radar/README.md)

| | Depth camera | 3D LiDAR |
|---|---|---|
| Range | 0.3–10 m | 5–200 m |
| Resolution | Dense (1080p+) | Sparse (16–128 lines) |
| RGB context | Yes | No |
| Outdoor sun | Stereo OK, ToF/IR struggles | Mostly fine, fragile in rain/fog |
| Cost | $100–$600 | $1,000–$80,000 |
| Field of view | 60–120° forward | 360° horizontal |

Rule of thumb: depth camera under 5 m, LiDAR over 5 m. Most modern robots use both.

---

## Going Deeper

- [REP-104 — Suffix Conventions for `camera_info`](https://www.ros.org/reps/rep-0104.html)
- [OpenCV camera calibration tutorial](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)
- [`image_pipeline` package](https://github.com/ros-perception/image_pipeline) — rectification, debayering, monocular calibration
- [Intel RealSense overview](https://www.realsenseai.com/compare-all-cameras/) — feature matrix across the D-series and Lidar L515
- [Stereolabs ZED documentation](https://www.stereolabs.com/docs/)
- [Luxonis DepthAI docs](https://docs.luxonis.com/)
- [Prophesee — event-based vision primer](https://www.prophesee.ai/event-camera-evk4/)
- [Hartley & Zisserman — *Multiple View Geometry in Computer Vision*](http://www.robots.ox.ac.uk/~vgg/hzbook/) — the textbook for camera geometry

https://www.youtube.com/watch?v=qByYk6JggQU

(Above: Two Minute Papers — event camera demo; mind-blowing if you've only seen frame cameras)
