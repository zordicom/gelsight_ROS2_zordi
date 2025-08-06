import cv2
import numpy as np
import os
import re
import asyncio
import subprocess
from threading import Thread, Lock

if os.name == 'nt':
    import winrt.windows.devices.enumeration as windows_devices

VIDEO_DEVICES = 4 # video device is labelled as 4 in windows

def get_camera_id(camera_name) -> int:
    """Find the camera ID that has the corresponding camera name."""
    cam_num = None
    working_cam_num = None
    if os.name == 'nt':
        cam_num = find_cameras_windows(camera_name)
    else:
        # For DIGIT cameras, hardcode to video5 since we know it works
        # if "DIGIT" in camera_name:
        #     print("Using hardcoded video5 for DIGIT camera")
        #     return 5
        
        # First pass: find all matching cameras and test them
        matching_cameras = []
        print(f"Looking for camera: '{camera_name}'")
        for file in os.listdir("/sys/class/video4linux"):
            real_file = os.path.realpath("/sys/class/video4linux/" + file + "/name")
            with open(real_file, "rt") as name_file:
                name = name_file.read().rstrip()
            print(f"Checking {file}: '{name}'")
            if camera_name in name:
                print(f"MATCH FOUND: '{camera_name}' in '{name}'")
                try:
                    cam_num = int(re.search(r"\d+$", file).group(0))
                    found = "FOUND!"
                    # Test if camera can be opened
                    test_cap = cv2.VideoCapture(cam_num)
                    if test_cap.isOpened():
                        test_cap.release()
                        print("{} {} -> {} (WORKING)".format(found, file, name))
                        working_cam_num = cam_num  # Store the working camera
                        matching_cameras.append((cam_num, file, name, True))
                    else:
                        test_cap.release()
                        print("{} {} -> {} (CAN'T OPEN)".format(found, file, name))
                        matching_cameras.append((cam_num, file, name, False))
                except Exception as e:
                    found = "ERROR"
                    print("{} {} -> {} (ERROR: {})".format(found, file, name, e))
            else:
                found = "      "
                print("{} {} -> {}".format(found, file, name))
        
        # Return the working camera if found, otherwise return the first matching one
        if working_cam_num is not None:
            cam_num = working_cam_num
        elif matching_cameras:
            # If no working camera found, use the first matching one
            cam_num = matching_cameras[0][0]
            print(f"Warning: No working camera found for {camera_name}, using first match: {matching_cameras[0][1]}")

    return cam_num

if os.name == 'nt':
    def find_cameras_windows(camera_name):
        allcams = get_camera_information(get_camera_indexes())# list of camera device
        
        if len(allcams) != 0:
            for cam in allcams:
                if camera_name in cam['camera_name']:
                    print("IGNORE PREVIOUS WARNING. It was just searching through all USB ports for the sensor.")
                    return cam['camera_index']
        
        print("Device is not in this list")
        print(allcams)
        import sys
        sys.exit()

    
    def get_camera_indexes():
        camera_indexes = []
    
        # the total number of possible USB camera is less than the total number of USBHub
        max_numbers_of_cameras_to_check = int(subprocess.getoutput("PowerShell -Command \"& {@(gwmi Win32_USBHub).count}\""))
        for index in range(max_numbers_of_cameras_to_check):
            capture = cv2.VideoCapture(index)
            if capture.read()[0]: # check if there is a camera connected to the index
                camera_indexes.append(index)
                capture.release()
        return camera_indexes
    
    def get_camera_information(camera_indexes: list) -> list:
        cameras_info = []

        cameras_info_windows = asyncio.run(get_camera_information_for_windows())

        for camera_index in camera_indexes:
            try:
                camera_name = cameras_info_windows.get_at(camera_index).name.replace('\n', '')
                cameras_info.append({'camera_index': camera_index, 'camera_name': camera_name})
            except:
                continue
        return cameras_info
    
    async def get_camera_information_for_windows():
        return await windows_devices.DeviceInformation.find_all_async(VIDEO_DEVICES)
    




class Camera2D:
    """The GelSight Camera Class. A mult-threaded wrapper around the cv2.VideoCapture"""
    def __init__(self, dev_type, imgh, imgw):
        self.name = dev_type
        self.dev_id = get_camera_id(dev_type)
        
        # Check if camera ID was found
        if self.dev_id is None:
            raise ValueError(f"Camera with name '{dev_type}' not found. Please check the device name in your configuration.")
        
        self.imgh = imgh
        self.imgw = imgw
        
        self.started = False
        self.read_lock = Lock()

        """Connect to the camera using cv2 streamer."""
        self.stream = cv2.VideoCapture(self.dev_id)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Set camera properties to reduce timeout issues
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # Add a small delay to ensure camera is ready
        import time
        time.sleep(1.0)  # Increased delay
        
        if self.stream is None or not self.stream.isOpened():
            raise RuntimeError(f"Unable to open video source: {self.dev_id}. Camera may be in use by another application.")
        
        # Try to read with timeout handling
        import threading
        import queue
        
        def read_with_timeout():
            try:
                return self.stream.read()
            except:
                return False, None
        
        # Use a thread with timeout
        result_queue = queue.Queue()
        thread = threading.Thread(target=lambda: result_queue.put(read_with_timeout()))
        thread.daemon = True
        thread.start()
        thread.join(timeout=3.0)  # 3 second timeout
        
        if thread.is_alive():
            # Thread is still running, timeout occurred
            print(f"Warning: Camera read timeout for device {self.dev_id}, but continuing...")
            self.grabbed, self.frame = False, None
        else:
            self.grabbed, self.frame = result_queue.get()
            
        # If initial read failed, try a few more times with shorter timeouts
        if not self.grabbed:
            print("Initial camera read failed, trying additional attempts...")
            for attempt in range(3):
                thread = threading.Thread(target=lambda: result_queue.put(read_with_timeout()))
                thread.daemon = True
                thread.start()
                thread.join(timeout=1.0)  # 1 second timeout
                
                if not thread.is_alive():
                    self.grabbed, self.frame = result_queue.get()
                    if self.grabbed:
                        print(f"Camera read successful on attempt {attempt + 2}")
                        break
                else:
                    print(f"Camera read timeout on attempt {attempt + 2}")

    def start(self):
        if self.started:
            print("already started!!")
            return None
        self.started = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self
    
    def update(self):
        while self.started:
            (grabbed, frame) = self.stream.read()
            self.read_lock.acquire()
            self.grabbed, self.frame = grabbed, frame
            self.read_lock.release()

    def read(self):
        self.read_lock.acquire()
        if self.frame is None:
            self.read_lock.release()
            return None
        frame = self.get_resize_crop(self.frame.copy())
        self.read_lock.release()
        return frame

    def stop(self):
        self.started = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join()
        if hasattr(self, 'stream') and self.stream is not None:
            self.stream.release()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()

    def get_resize_crop(self, img):
        """Resize and crop the image to the desired size."""
        if img is None:
            return None
        # remove 1/7th of border from each size
        border_size_x, border_size_y = int(img.shape[0] * (1 / 7)), int(
            np.floor(img.shape[1] * (1 / 7))
        )
        cropped_imgh = img.shape[0] - 2 * border_size_x
        cropped_imgw = img.shape[1] - 2 * border_size_y
        # Extra cropping to maintain aspect ratio
        extra_border_h = 0
        extra_border_w = 0
        if cropped_imgh * self.imgw / self.imgh > cropped_imgw + 1e-8:
            extra_border_h = int(cropped_imgh - cropped_imgw * self.imgh / self.imgw)
        elif cropped_imgh * self.imgw / self.imgh < cropped_imgw - 1e-8:
            extra_border_w = int(cropped_imgw - cropped_imgh * self.imgw / self.imgh)
        # keep the ratio the same as the original image size
        img = img[
            border_size_x + extra_border_h : img.shape[0] - border_size_x,
            border_size_y + extra_border_w : img.shape[1] - border_size_y,
        ]
        # final resize for 3d
        img = cv2.resize(img, (self.imgw, self.imgh))
        return img
    # def get_image(self, flush=False):
    #     """Get the image from the camera."""
    #     if flush:
    #         # flush out fist few frames to remove black frames
    #         for i in range(10):
    #             ret, f0 = self.cam.read()
    #     ret, f0 = self.cam.read()
    #     if ret:
    #         f0 = resize_crop(f0, self.imgw, self.imgh)
    #     else:
    #         print("ERROR! reading image from camera!")
    #     self.data = f0
    #     return self.data