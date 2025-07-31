This repo is largely based on a [working repo](https://github.com/joehjhuang/gs_sdk) from CMU's [Joe Huang](https://joehjhuang.github.io/).

This repo has made many significant and (imo) better adjustment to the official GelSight driver code, and we recommand that you use this instead of the official driver especially if you want to work with ROS2

# GelSight/DIGIT ROS2 Interface Setup

Quick setup for GelSight and DIGIT sensors in ROS2 Humble.

## Quick Start

### 1. Build the Package
```bash
cd ~/ros2_ws
colcon build --packages-select gelsight_capture
source install/setup.bash
```

### 2. Easy Sensor Swapping

**For DIGIT Sensor:**
```yaml
# In gsmini.yaml
device_name: "DIGIT: DIGIT"
# device_name: "GelSight Mini R0B 2DA7-P1FZ: Ge"
```

**For GelSight Sensor:**
```yaml
# In gsmini.yaml
# device_name: "DIGIT: DIGIT"
device_name: "GelSight Mini R0B 2DA7-P1FZ: Ge"
```

### 3. Run the Node
```bash
ros2 run gelsight_capture gelsight_image_server --ros-args -p config_path:=/home/zordi/ros2_ws/install/gelsight_capture/share/gelsight_capture/config/gsmini.yaml
```

### 4. View in RViz2
```bash
rviz2
```
Add →  By topic → add `/gelsight_capture/image` topic → Digit / Gelsight stream is displayed on the left of the screen

## Troubleshooting

**Camera not found:**
```bash
ls /dev/video* && cat /sys/class/video4linux/*/name
```

**Test camera directly:**
```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera available:', cap.isOpened()); cap.release()"
```

**Check topic data:**
```bash
ros2 topic hz /gelsight_capture/image
```

## File Structure

```
gelsight_ROS2_Zordi/
├── gelsight_capture/
│   ├── config/gsmini.yaml          # Main config file
│   ├── gelsight_capture/
│   │   ├── gelsight_image_server.py
│   │   └── gsdevice.py
│   └── package.xml
└── README.md
```

## Quick Commands

```bash
# Build after making any changes (changing sensor type in yaml)
colcon build --packages-select gelsight_capture

# Run
ros2 run gelsight_capture gelsight_image_server --ros-args -p config_path:=/home/zordi/ros2_ws/install/gelsight_capture/share/gelsight_capture/config/gsmini.yaml

# Monitor if the topic is publishing or not 
ros2 topic hz /gelsight_capture/image

# Visualize
rviz2
``` 
