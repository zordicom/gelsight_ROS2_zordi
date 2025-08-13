from cv_bridge import CvBridge
import cv2
import yaml
import signal
import sys

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from sensor_msgs.msg import Image

from .gsdevice import Camera2D


class GelsightImageServer(Node):
    def __init__(self):
        super().__init__('gelsight_image_client') # type: ignore
        
        ############################ Launch Parameters ########################################

        # it's complicated why we need to load the config path instead of the content of config. See launch file for explanation
        self.declare_parameter(name = 'config_path', value = '')
        self.declare_parameter(name='output_topic', value='/camera/gelsight')
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.imgh = config["h"]
            self.imgw = config["w"]

        ############################ Miscanellous Setup #######################################
        multithread_group = ReentrantCallbackGroup()
        self.cvbridge = CvBridge() # for converting ROS images to OpenCV images
        
        # the actual camera that captures the images
        self.camera2d = Camera2D(dev_type=config["device_name"], 
                                 imgh=self.imgh, 
                                 imgw=self.imgw)
        self.camera2d.start()

        ############################ Publisher Setup ###########################################
        # image publisher
        self.image_publisher = self.create_publisher(
        msg_type=Image, 
        topic=output_topic, 
        qos_profile=10)

        image_timer_period = 0.03  # in seconds. roughly 33 Hz
        self.image_timer = self.create_timer(
            timer_period_sec=image_timer_period, 
            callback=self.image_timer_callback,
            callback_group=multithread_group)

    #     # # Set up signal handler for graceful shutdown
    #     # signal.signal(signal.SIGINT, self.signal_handler)
    #     # signal.signal(signal.SIGTERM, self.signal_handler)

    # def signal_handler(self, signum, frame):
    #     """Handle Ctrl+C and other termination signals gracefully."""
    #     self.get_logger().info('Shutting down gracefully...')
    #     if hasattr(self, 'camera2d') and self.camera2d is not None:
    #         self.camera2d.stop()
    #         if hasattr(self.camera2d, 'stream') and self.camera2d.stream is not None:
    #             self.camera2d.stream.release()
    #     # Don't call rclpy.shutdown() here as it can cause issues
    #     # Let the main function handle shutdown properly
        
    def image_timer_callback(self):
        original_image = self.camera2d.read()
        # self.get_logger().info(f'image type: {type(original_image)}')
        if original_image is not None:
            ros_image = self.cvbridge.cv2_to_imgmsg(original_image, encoding='bgr8')
            self.image_publisher.publish(ros_image)
            
            # test to Save  images
            # cv2.imwrite(f"/tmp/test_gelsight_{self.get_clock().now().nanoseconds}.jpg", original_image)
        


def main(args=None):
    rclpy.init(args=args)

    server = GelsightImageServer()
    executor = MultiThreadedExecutor()
    executor.add_node(server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        server.get_logger().info('Keyboard interrupt received, shutting down...')
    finally:
        if hasattr(server, 'camera2d') and server.camera2d is not None:
            server.camera2d.stop()
            if hasattr(server.camera2d, 'stream') and server.camera2d.stream is not None:
                server.camera2d.stream.release()
        server.destroy_node()
        
        # ✅ Only shutdown if not already shut down
        if rclpy.ok():  
            rclpy.shutdown()

if __name__ == '__main__':
    main()
