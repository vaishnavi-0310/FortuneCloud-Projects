import os
import sys
import logging
from io import BytesIO
from urllib.parse import quote_plus

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from sqlalchemy import create_engine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def get_env(name: str, required: bool = True, default: str = None) -> str:
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def pandas_dtype_to_glue(dtype) -> str:
    dtype_str = str(dtype).lower()

    if "int" in dtype_str:
        return "bigint"
    if "float" in dtype_str:
        return "double"
    if "bool" in dtype_str:
        return "boolean"
    if "datetime" in dtype_str:
        return "timestamp"
    return "string"


def read_csv_from_s3(s3_client, bucket: str, key: str) -> pd.DataFrame:
    logger.info("Reading CSV from S3: s3://%s/%s", bucket, key)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read()
    df = pd.read_csv(BytesIO(content))
    logger.info("CSV loaded successfully. Rows=%s, Columns=%s", len(df), len(df.columns))
    return df


def build_rds_engine():
    rds_host = get_env("RDS_HOST")
    rds_port = get_env("RDS_PORT", required=False, default="3306")
    rds_db = get_env("RDS_DB_NAME")
    rds_user = get_env("RDS_USERNAME")
    rds_password = get_env("RDS_PASSWORD")

    safe_password = quote_plus(rds_password)
    connection_string = (
        f"mysql+pymysql://{rds_user}:{safe_password}@{rds_host}:{rds_port}/{rds_db}"
    )
    engine = create_engine(connection_string, pool_pre_ping=True)
    return engine


def load_to_rds(df: pd.DataFrame, table_name: str):
    logger.info("Trying to load data into RDS table: %s", table_name)
    engine = build_rds_engine()

    with engine.begin() as connection:
        df.to_sql(
            name=table_name,
            con=connection,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )

    logger.info("Data inserted into RDS successfully.")


def ensure_glue_database(glue_client, database_name: str):
    try:
        glue_client.get_database(Name=database_name)
        logger.info("Glue database already exists: %s", database_name)
    except glue_client.exceptions.EntityNotFoundException:
        logger.info("Creating Glue database: %s", database_name)
        glue_client.create_database(
            DatabaseInput={
                "Name": database_name,
                "Description": "Project 5 fallback database for S3 CSV metadata"
            }
        )
        logger.info("Glue database created: %s", database_name)


def build_glue_columns(df: pd.DataFrame):
    columns = []
    for col_name, dtype in df.dtypes.items():
        columns.append(
            {
                "Name": str(col_name).lower().replace(" ", "_"),
                "Type": pandas_dtype_to_glue(dtype)
            }
        )
    return columns


def get_s3_folder_location(bucket: str, key: str) -> str:
    if "/" in key:
        prefix = key.rsplit("/", 1)[0] + "/"
    else:
        prefix = ""
    return f"s3://{bucket}/{prefix}"


def create_or_update_glue_table(glue_client, database_name: str, table_name: str, df: pd.DataFrame, bucket: str, key: str):
    s3_location = get_s3_folder_location(bucket, key)
    columns = build_glue_columns(df)

    table_input = {
        "Name": table_name.lower(),
        "Description": "Fallback external table created by Project 5 Docker app",
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "csv",
            "skip.header.line.count": "1",
            "typeOfData": "file",
            "delimiter": ","
        },
        "StorageDescriptor": {
            "Columns": columns,
            "Location": s3_location,
            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
                "Parameters": {
                    "field.delim": ",",
                    "skip.header.line.count": "1"
                }
            }
        }
    }

    try:
        glue_client.get_table(DatabaseName=database_name, Name=table_name.lower())
        logger.info("Glue table exists. Updating table: %s.%s", database_name, table_name.lower())
        glue_client.update_table(
            DatabaseName=database_name,
            TableInput=table_input
        )
        logger.info("Glue table updated successfully.")
    except glue_client.exceptions.EntityNotFoundException:
        logger.info("Creating Glue table: %s.%s", database_name, table_name.lower())
        glue_client.create_table(
            DatabaseName=database_name,
            TableInput=table_input
        )
        logger.info("Glue table created successfully.")

    logger.info("Glue table points to S3 location: %s", s3_location)


def fallback_to_glue(df: pd.DataFrame, bucket: str, key: str):
    glue_database = get_env("GLUE_DATABASE_NAME")
    glue_table = get_env("GLUE_TABLE_NAME")

    glue_client = boto3.client("glue", region_name=get_env("AWS_REGION"))
    ensure_glue_database(glue_client, glue_database)
    create_or_update_glue_table(glue_client, glue_database, glue_table, df, bucket, key)


def main():
    aws_region = get_env("AWS_REGION")
    s3_bucket = get_env("S3_BUCKET_NAME")
    s3_key = get_env("S3_FILE_KEY")
    rds_table_name = get_env("RDS_TABLE_NAME")

    logger.info("Starting Project 5 ingestion pipeline")
    logger.info("Region: %s", aws_region)

    s3_client = boto3.client("s3", region_name=aws_region)

    df = read_csv_from_s3(s3_client, s3_bucket, s3_key)

    try:
        load_to_rds(df, rds_table_name)
        logger.info("Pipeline completed successfully using RDS.")
    except Exception as rds_error:
        logger.exception("RDS load failed. Switching to Glue fallback. Error: %s", rds_error)
        fallback_to_glue(df, s3_bucket, s3_key)
        logger.info("Pipeline completed using Glue fallback.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Pipeline failed completely: %s", exc)
        sys.exit(1)
