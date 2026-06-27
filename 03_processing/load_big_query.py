# 03_processing/load_bigquery.py

from google.cloud import bigquery
from config import BQ_DATASET, PROJECT_ID
from google.oauth2 import service_account

def get_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)

def upload_dataframe(df, table_name: str) -> None:
    client = get_client()

    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{table_name}"

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    )

    job.result()
