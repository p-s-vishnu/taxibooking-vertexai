import logging
from typing import Dict, List, Union

from google.cloud import aiplatform, bigquery
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

def add_traffic_last_5min(instance, dataset="taxifare", table="traffic_realtime"):
    """ Adds the dynamic feature `traffic_last_5min` to the instance
    """
    bq = bigquery.Client()
    query_string = f"""
    SELECT
      *
    FROM
      `{dataset}.{table}`
    ORDER BY
      time DESC
    LIMIT 1
    """
    trips = bq.query(query_string).to_dataframe()["trips_last_5min"][0]
    instance["traffic_last_5min"] = int(trips)
    return instance

def predict(
    project: str,
    endpoint_id: str,
    instances: Union[Dict, List[Dict]],
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
):
    """
    `instances` can be either single instance of type dict or a list
    of instances.

    Reference: https://github.com/googleapis/python-aiplatform/blob/master/samples/snippets/predict_custom_trained_model_sample.py
    """
    client_options = {"api_endpoint": api_endpoint}     # f"{REGION}-aiplatform.googleapis.com"
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    
    instances = instances if type(instances) == list else [instances]
    instances = [add_traffic_last_5min(instance_dict) for instance_dict in instances]
    instances = [
        json_format.ParseDict(instance_dict, Value()) for instance_dict in instances
    ]
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )
    logging.info("response")
    logging.info(f" deployed_model_id: {response.deployed_model_id}")
    
    # The predictions are a google.protobuf.Value representation of the model's predictions.
    predictions = response.predictions
    for prediction in predictions:
        logging.info(" prediction:", dict(prediction))
