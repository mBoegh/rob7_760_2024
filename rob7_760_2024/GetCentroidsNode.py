from rob7_760_2024.LIB import JSON_Handler

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
import sensor_msgs_py.point_cloud2 as pc2

import numpy as np
from sklearn.cluster import DBSCAN


class GetCentroidsNode(Node):
    def __init__(self, distance_threshold, eps, min_samples, merge_threshold, obstacle_threshold):
        # Initializing parsed variables.
        self.DISTANCE_THRESHOLD = distance_threshold
        self.EPS = eps
        self.MIN_SAMPLES = min_samples
        self.MERGE_THRESHOLD = merge_threshold
        self.OBSTACLE_THRESHOLD = obstacle_threshold
        
        # Initializing the 'Node' class, from which this class is inheriting, with argument 'node_name'.
        Node.__init__(self, 'get_centroids_node')
        self.logger = self.get_logger()

        # Example logging to show node is active
        self.logger.debug("Hello world!")
        self.logger.info("Hello world!")
        self.logger.warning("Hello world!")
        self.logger.error("Hello world!")
        self.logger.fatal("Hello world!")
        
        # Subscribe to the 3D points topic from object_det_cloud
        self.point_sub = self.create_subscription(
            PointCloud2, '/transformed_points', self.transformed_points_callback, 10)

        # Subscribe to the obstacles cloud topic from SegmentationNode
        self.timestamp_sub = self.create_subscription(
            PointCloud2, '/cloud_obstacles', self.cloud_obstacles_callback, 10)

        # Publisher for the filtered points as PointCloud2
        self.point_cloud_pub = self.create_publisher(PointCloud2, '/centroids', 10)

        # Lists to store points from the topics
        self.transformed_points = []
        self.cloud_obstacles = []

        self.logger.info("GetCentroids Node initialized.")

    def transformed_points_callback(self, msg):
        """
        Callback to handle transformed points.
        Extracts x, y, z, and label_id from the incoming PointCloud2 message.
        """
        self.transformed_points = list(pc2.read_points(
            msg, field_names=["x", "y", "z", "label"], skip_nans=True))
        self.logger.debug(f"Received {len(self.transformed_points)} transformed points.")

    def cloud_obstacles_callback(self, msg):
        """
        Callback to handle cloud obstacles.
        Extracts x, y, and z from the incoming PointCloud2 message.
        """
        self.cloud_obstacles = list(pc2.read_points(
            msg, field_names=["x", "y", "z"], skip_nans=True))
        self.logger.debug(f"Received {len(self.cloud_obstacles)} obstacle points.")

        # Once obstacles are received, process and publish the filtered points
        self.process_and_publish_centroids()

    def process_and_publish_centroids(self):
        """
        Process the points to compute centroids for subclusters based on label_id.
        """
        if not self.transformed_points or not self.cloud_obstacles:
            if not self.transformed_points and not self.cloud_obstacles:
                self.logger.warning("No data to process. Waiting for both topics.")
            elif not self.transformed_points:
                self.logger.warning("No data to process. Waiting for transformed_points.")
            elif not self.cloud_obstacles:
                self.logger.warning("No data to process. Waiting for cloud_obstacles.")
            return

        # Convert obstacle points to numpy array for efficient distance computation
        obstacle_array = np.array([[p[0], p[1], p[2]] for p in self.cloud_obstacles])

        # Filter transformed points based on proximity to obstacles
        filtered_points = []
        for point in self.transformed_points:
            x, y, z, label_id = point
            distances = np.linalg.norm(obstacle_array - np.array([x, y, z]), axis=1)
            if np.any(distances < self.DISTANCE_THRESHOLD):
                filtered_points.append((x, y, z, label_id))

        self.logger.fatal(f"from {len(self.transformed_points)} Filtered down to {len(filtered_points)} points near obstacles.")

        if not filtered_points:
            self.logger.warning("No points to cluster after filtering.")
            return

        # Perform clustering and compute centroids
        centroids = self.compute_centroids(filtered_points)

        # Merge centroids if they are too close
        centroids = self.merge_close_centroids(centroids, merge_threshold=self.MERGE_THRESHOLD, obstacle_threshold=self.OBSTACLE_THRESHOLD)

        # Publish the centroids
        self.publish_centroids(centroids)

    def compute_centroids(self, filtered_points):
        """
        Perform DBSCAN clustering within each label group and compute centroids.

        Args:
            filtered_points (list): List of tuples [(x, y, z, label_id), ...]

        Returns:
            list: List of centroids [(x, y, z, label_id), ...].
        """
        # Group points by label_id
        clusters_by_label = {}
        for point in filtered_points:
            x, y, z, label_id = point
            clusters_by_label.setdefault(label_id, []).append((x, y, z))

        centroids = []

        # Perform DBSCAN clustering and compute centroids for each label group
        for label_id, points in clusters_by_label.items():
            points_array = np.array(points)

            # Apply DBSCAN clustering
            dbscan = DBSCAN(eps=self.EPS, min_samples=self.MIN_SAMPLES)
            labels = dbscan.fit_predict(points_array)

            # Organize points into subclusters
            subclusters = {}
            for idx, subcluster_id in enumerate(labels):
                if subcluster_id != -1:  # Ignore noise points
                    subclusters.setdefault(subcluster_id, []).append(points[idx])

            # Compute centroids for each subcluster
            for subcluster_id, subcluster_points in subclusters.items():
                subcluster_array = np.array(subcluster_points)
                centroid = np.mean(subcluster_array, axis=0)  # Mean of x, y, z
                centroids.append((*centroid, label_id))  # Add label_id to centroid

        return centroids

    def merge_close_centroids(self, centroids, merge_threshold=0.2, obstacle_threshold=0.2):
        """
        Merge centroids that are too close to each other based on a threshold.
        The merged centroid will only be added if it is near enough to any obstacle point.
        The non-merged centroids will be retained.

        Args:

def generate_launch_description():

    param = [{
            centroids (list): List of centroids [(x, y, z, label_id), ...].
            merge_threshold (float): Distance threshold for merging centroids (meters).
            obstacle_threshold (float): Distance threshold for checking if the merged centroid is near an obstacle.

        Returns:
            list: List of merged centroids [(x, y, z, label_id), ...].
        """
        merged_centroids = []
        # Convert obstacle points to numpy array for efficient distance computation
        obstacle_array = np.array([[p[0], p[1], p[2]] for p in self.cloud_obstacles])

        # Group centroids by label_id
        centroids_by_label = {}
        for centroid in centroids:
            x, y, z, label_id = centroid
            centroids_by_label.setdefault(label_id, []).append(np.array([x, y, z]))

        # Process each group of centroids with the same label
        for label_id, group_centroids in centroids_by_label.items():
            group_centroids = np.array(group_centroids)
            temp_merged = []

            while len(group_centroids) > 0:
                current = group_centroids[0]
                distances = np.linalg.norm(group_centroids - current, axis=1)

                # Find centroids within merge threshold
                close_indices = np.where(distances < merge_threshold)[0]
                close_centroids = group_centroids[close_indices]

                # Compute average (middle) centroid
                avg_centroid = np.mean(close_centroids, axis=0)

                # Check if the merged centroid is near any obstacle
                is_near_obstacle = np.any(np.linalg.norm(obstacle_array - avg_centroid, axis=1) < obstacle_threshold)

                # If the merged centroid is near an obstacle, keep the merged centroid
                if is_near_obstacle:
                    temp_merged.append((*avg_centroid, label_id))
                else:
                    # If the merged centroid is not near an obstacle, keep the original centroids
                    temp_merged.extend([(*c, label_id) for c in close_centroids])

                # Remove the centroids that were merged from the group
                group_centroids = np.delete(group_centroids, close_indices, axis=0)

            merged_centroids.extend(temp_merged)

        return merged_centroids

    def publish_centroids(self, centroids):
        """
        Publish the centroids as a PointCloud2 message.
        """
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = "map"  # Replace with the appropriate frame

        # Define the fields for the new PointCloud2
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='label', offset=12, datatype=PointField.UINT32, count=1),
        ]

        # Serialize the centroids into a PointCloud2 message
        centroid_cloud = pc2.create_cloud(header, fields, centroids)

        # Publish the centroid point cloud
        self.point_cloud_pub.publish(centroid_cloud)
        self.get_logger().info(f"Published centroid point cloud: '{centroid_cloud}'")
    
def main():
    # Path for 'settings.json' file
    json_file_path = ".//rob7_760_2024//settings.json"
    
    # Instance the 'JSON_Handler' class for interacting with the 'settings.json' file
    json_handler = JSON_Handler(json_file_path)
    
    # Get settings from 'settings.json' file
    NODE_LOG_LEVEL = "rclpy.logging.LoggingSeverity." + json_handler.get_subkey_value("GetCentroidsNode", "NODE_LOG_LEVEL")
    DISTANCE_THRESHOLD = json_handler.get_subkey_value("GetCentroidsNode", "DISTANCE_THRESHOLD")
    EPS = json_handler.get_subkey_value("GetCentroidsNode", "EPS")
    MIN_SAMPLES = json_handler.get_subkey_value("GetCentroidsNode", "MIN_SAMPLES")
    MERGE_THRESHOLD = json_handler.get_subkey_value("GetCentroidsNode", "MERGE_THRESHOLD")
    OBSTACLE_THRESHOLD = json_handler.get_subkey_value("GetCentroidsNode", "OBSTACLE_THRESHOLD")

    # Initialize the rclpy library.
    rclpy.init()
    
    # Sets the logging level of importance. 
    # When setting, one is setting the lowest level of importance one is interested in logging.
    # Logging level is defined in settings.json.
    # Logging levels:
    # - DEBUG
    # - INFO
    # - WARNING
    # - ERROR
    # - FATAL
    # The eval method interprets a string as a command.
    rclpy.logging.set_logger_level("main", eval(NODE_LOG_LEVEL))
    
    # Instance the Main class
    get_centroids_node = GetCentroidsNode(DISTANCE_THRESHOLD, EPS, MIN_SAMPLES, MERGE_THRESHOLD, OBSTACLE_THRESHOLD)
    
    # Begin looping the node
    try:
        rclpy.spin(get_centroids_node)
    except KeyboardInterrupt:
        get_centroids_node.logger.info("Shutting down GetCentroidsNode.")

    finally:
        get_centroids_node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()