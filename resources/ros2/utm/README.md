# Ubuntu in UTM — config for bit2atms ROS2 course

Assumes you already have Ubuntu **24.04 LTS (Noble) ARM64** running in UTM on your Mac. ROS2 Jazzy ships official packages for 24.04 only — 22.04 and 26.04 will not work with the apt commands below.

This doc covers the UTM-specific tweaks and the ROS2 install for ch01–ch03. Nothing else.

---

## 1. UTM settings to verify (VM powered off)

Edit VM → check these:

| Setting | Required value | Why |
|---|---|---|
| System → Memory | 8 GB minimum (12 GB if your Mac has 16 GB+) | Gazebo + RViz + Nav2 + your editor |
| System → CPU Cores | 4 minimum | Gazebo physics is multi-threaded |
| Display → **Hardware OpenGL Acceleration** | **Enabled (✅)** | Without this, Gazebo runs in software mode and is unusably slow — biggest source of "Gazebo is broken" bug reports |
| Sharing → Directory Share Mode | **VirtFS** | What the `fstab` line below assumes |
| Sharing → Path | Browse and select your `bit2atms` repo on the Mac (e.g. `/Users/you/code/bit2atms`) | The bridge between Mac and VM |

UTM's QEMU backend exposes VirtFS shares with the hardcoded tag **`share`** regardless of the path you pick — that's what the `fstab` line below uses. (The "Path" placeholder text in UTM's dialog is just a hint, not the tag.) Also install the SPICE guest agent inside the VM (`sudo apt install -y spice-vdagent`) — UTM's Sharing dialog notes that VirtFS needs device drivers; on Ubuntu 24.04 the 9p kernel module is built-in but the SPICE agent is still needed for clipboard sharing.

Power the VM back on after changes.

---

## 2. Mount the Mac shared folder

Inside the VM, open a terminal:

```bash
sudo apt install -y spice-vdagent
sudo mkdir -p /mnt/bit2atms
echo "share /mnt/bit2atms 9p trans=virtio,version=9p2000.L,rw,_netdev 0 0" | sudo tee -a /etc/fstab
sudo mount -a

# Verify — should list your repo contents (courses/, workspace/, reader.html, ...)
ls /mnt/bit2atms
```

If `ls /mnt/bit2atms` is empty, the share tag in your kernel doesn't match what's in `fstab`. Check the actual tag UTM is exposing:

```bash
sudo cat /sys/bus/virtio/devices/*/mount_tag 2>/dev/null
```

This prints whatever string the hypervisor is broadcasting. For UTM's QEMU backend it's almost always `share` (which is what the `fstab` line above uses). If you see something else, replace `share` in the `fstab` line with that string, then `sudo mount -a` again.

`sudo dmesg | grep 9p` showing `no channels available for device <name>` means the kernel tried to mount the wrong tag — same fix.

For convenience:

```bash
ln -s /mnt/bit2atms ~/bit2atms
```

From here on, `~/bit2atms` in the VM === your repo on the Mac. Edit on Mac, run in VM.

---

## 3. Install ROS2 Jazzy + course dependencies

```bash
# Locale (ROS2 requires UTF-8)
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8

# Add the ROS2 apt repo
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS2 desktop + everything ch01–ch03 need
sudo apt update
sudo apt install -y \
  ros-jazzy-desktop \
  python3-colcon-common-extensions \
  ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations \
  ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-teleop \
  ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox \
  ros-jazzy-rviz2 ros-jazzy-tf2-tools ros-jazzy-tf2-ros
```

---

## 4. Auto-source ROS2 in every shell

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

---

## 5. Verify

```bash
ros2 pkg list | grep -E "turtlebot3_gazebo|nav2_bringup|slam_toolbox"
```

Expected:

```text
nav2_bringup
slam_toolbox
turtlebot3_gazebo
```

Smoke test — should open a Gazebo window with a TurtleBot3:

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Ctrl+C in the terminal to close. If Gazebo opens but the simulation runs at <1 FPS, OpenGL acceleration is off — see Step 1.

---

## 6. Snapshot the VM

In UTM (Mac side, VM powered off): **Edit → Drives → Take Snapshot**, name it `clean-jazzy-installed`. Roll back here if you ever wreck the VM.

---

## Day-to-day

- Boot VM, open a terminal.
- `cd ~/bit2atms/workspace/ros2/ch02` — your code lives on the Mac, edit it from any Mac editor.
- Run `ros2 launch ...` etc. inside the VM.
- Suspend VM (UTM → Pause) when done — resume is instant.

---

## Troubleshooting

- **Gazebo is slow / blank window** — Hardware OpenGL Acceleration is disabled (Step 1).
- **Shared folder is empty / `dmesg` says "no channels available for device …"** — fstab uses the wrong tag. UTM's QEMU backend uses tag `share`, not the directory basename or any custom value. Confirm with `sudo cat /sys/bus/virtio/devices/*/mount_tag` and update fstab to match.
- **`ros2 launch` says command not found** — Step 4 didn't take. Check `tail ~/.bashrc` shows the source/export lines, open a fresh terminal.
- **`Package 'ros-jazzy-desktop' has no installation candidate`** — Not on Ubuntu 24.04. `lsb_release -a` should show Noble.
