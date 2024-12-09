from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.actions import SetParameter


def generate_launch_description():

    param = [{
        'subscribe_depth': True,
        'subscribe_rgb': True,
        'subscribe_odom_info': True,
        'approx_sync': True,
        'rgb_frame_id': 'head_front_camera_rgb_frame',  # RGB camera frame
        'depth_frame_id': 'head_front_camera_depth_frame',  # Depth camera frame
        'frame_id': 'base_link',
        'odom_frame_id': 'odom',
        'use_sim_time':True,
        'RGBD/MaxDepth': 8.0,
        'RGBD/MinDepth': 0.6,
        'imu_frame_id':'base_imu_link',
        #'RGBD/frameRate' : 15.0,
    }]

    remappings = [
        # camera param
        ('rgb/image', '/head_front_camera/rgb/image_raw'),
        ('depth/image', '/head_front_camera/depth_registered/image_raw'),
        ('rgb/camera_info', '/head_front_camera/rgb/camera_info'),

        # imu to improve odometry
        ('imu', '/imu_sensor_broadcaster/imu'),
        
        ]


    return LaunchDescription([

        Node(
            package='rtabmap_odom', executable='rgbd_odometry', output='screen',
            parameters=param,
            remappings=remappings),
    
        Node(
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=param,
            remappings=remappings,
            arguments=['-d']),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=param,
            remappings=remappings),    

        Node(
            package='depth_image_proc', executable='point_cloud_xyzrgb', output='screen',
            remappings=[
                ('depth', ''),
                ('rgb', '/head_front_camera/rgb/image_raw'),
                ('point_cloud', 'segmented/pointcloud')
                
            ]
            
        ),
        
        Node(
            package='octomap_server', executable='octomap_server_node', name='segmented_map', output='screen',
            parameters=[{
                    'resolution': 0.05,
                    'frame_id': 'map',}],
            remappings=[
                    ('cloud_in', 'segmented/pointcloud')]
            ),
    ])
