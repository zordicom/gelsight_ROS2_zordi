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
# device_name: "GelSight Mini R0B 2D04-CPXB: Ge"
```

**For GelSight Sensor:**
```yaml
# In gsmini.yaml
# device_name: "DIGIT: DIGIT"
device_name: "GelSight Mini R0B 2D04-CPXB: Ge"
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

## Available Topics

- `/gelsight_capture/image` - Raw camera images
- `/gelsight_capture/pointcloud` - 3D pointcloud data

## Troubleshooting

### **Step 1: Basic Checks**

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

### **Step 2: Camera Lock Issues (If you get "Camera not found" error after connecting sensor)**

If you get the "Camera not found" error even after connecting the sensor, follow these steps:

**1. Check for processes using cameras:**
```bash
lsof /dev/video*
ps aux | grep gelsight
ps aux | grep ros2
```

**2. Kill all camera-related processes:**
```bash
pkill -f ros2
pkill -f python
pkill -f gelsight
pkill -f opencv
```

**3. Reset camera modules:**
```bash
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo
```

**4. Check camera permissions:**
```bash
ls -l /dev/video*
sudo chmod 666 /dev/video*
```

**5. Test camera availability:**
```bash
python3 -c "import cv2; cap = cv2.VideoCapture(5); print('Video5 available:', cap.isOpened()); cap.release()"
```

**6. Quick reset command:**
```bash
pkill -f ros2 && pkill -f python && sudo modprobe -r uvcvideo && sudo modprobe uvcvideo
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

## Current Status: ✅ WORKING

- **GelSight Mini R0B 2D04-CPXB: Ge** - Detected and working
- **Publishing at ~20Hz** - Stable data stream
- **RViz2 visualization** - Available
- **Easy sensor swapping** - Comment/uncomment in config 