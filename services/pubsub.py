import logging
from google import api_core
from google.cloud import pubsub_v1 as pubsub


def get_pubsub_client(gcp_project_id, topic="taxi_rides"):
    """ Get the topic if already exists or else create a new one
    """
    publisher = pubsub.PublisherClient()
    topic_name = publisher.topic_path(gcp_project_id, topic)
    try:
        publisher.get_topic(topic_name)
        logging.info("Reusing pub/sub topic %s", topic)
    except api_core.exceptions.NotFound:
        publisher.create_topic(topic_name)
        logging.info("Creating pub/sub topic %s", topic)
    return publisher
