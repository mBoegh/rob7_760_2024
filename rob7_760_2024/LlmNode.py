from rob7_760_2024.LIB import JSON_Handler
     
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

import os
from openai import OpenAI


class LlmNode(Node):
    """
    This is the LLM node of the ROS2 network.
    """

    def __init__(self, llm_model, llm_content):

        # Initialising parsed variables.
        self.LLM_MODEL = llm_model
        self.LLM_CONTENT = llm_content
        
        # Assuming the OpenAI API key is set as an environment variable
        self.OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

        self.client = OpenAI(api_key=self.OPENAI_API_KEY)


        # Initialising the 'Node' class, from which this class is inheriting, with argument 'node_name'.
        Node.__init__(self, 'llm_node')
        self.logger = self.get_logger()

        # This is the ROS2 Humble logging system, which is build on the Logging module for Python.
        # It displays messages with developer specified importance.
        # Here all the levels of importance are used to indicate that the script is running.
        self.logger.debug("Hello world!")
        self.logger.info("Hello world!")
        self.logger.warning("Hello world!")
        self.logger.error("Hello world!")
        self.logger.fatal("Hello world!")

        self.trigger = False

        # Initialising a publisher to the topic '/object_list'.
        # On this topic is expected data of type std_msgs.msg.String which is imported as String.
        # The '10' argument is some Quality of Service parameter (QoS).
        self.object_list_publisher = self.create_publisher(String, '/object_list', 10)
        self.object_list_publisher  # prevent unused variable warning

        self.object_list_msg = String()
        
        self.trigger_subscriber = self.create_subscription(Bool, '/trigger2', self.trigger_callback, 10)

        self.user_input_subscriber = self.create_subscription(String, '/user_input', self.user_input_callback, 10)
        
        #########################
        ### Example Publisher ###
        #########################
        
        #     # Initialising a publisher to the topic 'example'.
        #     # On this topic is expected data of type std_msgs.msg.* which is imported as *.
        #     # The '10' argument is some Quality of Service parameter (QoS).
        #     self.example_publisher = self.create_publisher(String, 'example', 10)
        #     self.example_publisher_publisher  # prevent unused variable warning

        # self.example_msg = String()

        ######################
        ### End of example ###
        ######################
        


        ##########################
        ### Example Subscriber ###
        ##########################

        #    # Initialising a subscriber to the topic 'example'.
        #    # On this topic is expected data of type std_msgs.msg.* which is imported as *.
        #    # The subscriber calls a defined callback function upon message recieval from the topic.
        #    # The '10' argument is some Quality of Service parameter (QoS).
        #    self.example_subscription = self.create_subscription(String, 'example', self.example_topic_callback, 10)
        #    self.example_subscription  # prevent unused variable warning


        # def example_topic_callback(self, msg):
        #    """
        #    Callback function called whenever a message is recieved on the subscription 'example_subscription'
        #    """

        #    self.logger.debug(f"Recieved data '{msg.data}'")


        ######################
        ### End of example ###
        ######################

        self.logger.fatal("Waiting for trigger.")


    def trigger_callback(self, msg):
        self.logger.fatal(f"Received data '{msg.data}'")
        
        if msg.data == True:
            self.trigger = True


    def user_input_callback(self, msg):
        # The callback function called during each period of the timer.
        
        self.logger.fatal(f"Received user_input message: '{msg.data}'")
        
        if self.trigger == True:

            self.response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.LLM_CONTENT
                    },
                    {"role": "user", "content": msg.data},
                ],
                model=self.LLM_MODEL,
            )

            # Accessing the content directly as an attribute
            self.parsed_locations = self.response.choices[0].message.content
            self.logger.debug(f"parsed_locations: {self.parsed_locations}")

            self.object_list_msg.data = self.parsed_locations
            self.logger.debug(f"object_list_msg.data: {self.object_list_msg.data}")

            self.object_list_publisher.publish(self.object_list_msg)
            self.logger.debug(f"'object_list_publisher' published message to topic 'object_list'.")

        else:
            self.logger.fatal(f"Not yet triggered.")

####################
######  MAIN  ######
####################


def main():
    
    # Path for 'settings.json' file
    json_file_path = ".//rob7_760_2024//settings.json"

    # Instance the 'JSON_Handler' class for interacting with the 'settings.json' file
    json_handler = JSON_Handler(json_file_path)
    
    # Get settings from 'settings.json' file
    LLM_MODEL = json_handler.get_subkey_value("LlmNode", "LLM_MODEL")
    LLM_CONTENT = json_handler.get_subkey_value("LlmNode", "LLM_CONTENT")
    NODE_LOG_LEVEL = "rclpy.logging.LoggingSeverity." + json_handler.get_subkey_value("LlmNode", "NODE_LOG_LEVEL")

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
    rclpy.logging.set_logger_level("llm_node", eval(NODE_LOG_LEVEL))
    
    # Instance the LLM class
    llm_node = LlmNode(LLM_MODEL, LLM_CONTENT)

    # Begin looping the node
    rclpy.spin(llm_node)
    

if __name__ == "__main__":
    main()