import logging
from google import api_core
from google.cloud import bigquery


def create_dataset(dataset_id="taxifare"):
    bq = bigquery.Client()
    dataset = bigquery.Dataset(bq.dataset(dataset_id))
    try:
        bq.create_dataset(dataset)  # will fail if dataset already exists
        logging.info("Dataset created.")
    except api_core.exceptions.Conflict:
        logging.info("Dataset already exists.")

def create_table(dataset_id="taxifare", table_name="traffic_realtime"):
    bq = bigquery.Client()
    dataset = bigquery.Dataset(bq.dataset(dataset_id))
    table_ref = dataset.table(table_name)
    SCHEMA = [
        bigquery.SchemaField("trips_last_5min", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
    ]
    table = bigquery.Table(table_ref, schema=SCHEMA)
    try:
        bq.create_table(table)
        logging.info("Table created.")
    except api_core.exceptions.Conflict:
        logging.info("Table already exists.")