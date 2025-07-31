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
ros2 run rviz2 rviz2
```
Add Image display → set topic to `/gelsight_capture/image`

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
gelsight_ROS2_interface/
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
# Build
colcon build --packages-select gelsight_capture

# Run
ros2 run gelsight_capture gelsight_image_server --ros-args -p config_path:=/home/zordi/ros2_ws/install/gelsight_capture/share/gelsight_capture/config/gsmini.yaml

# Monitor
ros2 topic hz /gelsight_capture/image

# Visualize
ros2 run rviz2 rviz2
``` 