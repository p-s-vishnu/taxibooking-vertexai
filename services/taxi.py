from .pubsub import get_pubsub_client

import random
import logging
import time


def generate_trips(project_id, topic):
    publisher = get_pubsub_client(gcp_project_id=project_id, topic=topic)
    while True:
        num_trips = random.randint(10, 60)
        for _ in range(num_trips):
            publisher.publish(topic, b"taxi_ride")
        logging.info("Publishing: %s", time.ctime())
        time.sleep(5)
