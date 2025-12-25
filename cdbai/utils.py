from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional, Sequence

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from google.api_core.exceptions import BadRequest
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

from .normalize_prompt import normalize_prompt

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS: Sequence[str] = (
    "GOOGLE_PROJECT_ID",
    "GOOGLE_DATASET",
    "GOOGLE_TABLE",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "LITELLM_PROXY_API_BASE",
    "LITELLM_PROXY_API_KEY",
    "USE_LITELLM_PROXY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_S3_BUCKET",
    "AWS_DEFAULT_REGION",
    "FORCED_SQL_LIMIT",
    "FAST_LLM",
    "SMART_LLM",
)


def get_forced_sql_limit() -> int:
    """Read the forced SQL limit from the environment.

    Returns:
        The integer value of ``FORCED_SQL_LIMIT``.

    Raises:
        MissingEnvironmentVariableError: When ``FORCED_SQL_LIMIT`` is unset/blank.
        ValueError: When ``FORCED_SQL_LIMIT`` cannot be parsed as an integer.
    """
    raw = os.environ.get("FORCED_SQL_LIMIT")
    if raw is None or not raw.strip():
        raise MissingEnvironmentVariableError(
            "Missing required environment variables: FORCED_SQL_LIMIT. Aborting."
        )
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"FORCED_SQL_LIMIT must be an integer, got {raw!r}")


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when required environment variables are missing."""


def make_bq_client(connection_info: dict) -> bigquery.Client:
    project = connection_info["project_id"]
    creds = connection_info.get("credentials")

    return bigquery.Client(
        project=project,
        credentials=creds,
    )


def check_required_env_vars() -> None:
    """Ensure the runtime environment exposes all required variables.

    Raises:
        MissingEnvironmentVariableError: When one or more required variables
            are not present (or empty) in ``os.environ``.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        missing_list = ", ".join(missing)
        raise MissingEnvironmentVariableError(
            f"Missing required environment variables: {missing_list}. Aborting."
        )
    logger.info("All required environment variables present")


def get_default_table_fqn() -> str:
    """Return the canonical dataset.table identifier for the default dataset.

    Returns:
        Fully-qualified table identifier in ``dataset.table`` format.
    """
    dataset = os.environ["GOOGLE_DATASET"]
    table = os.environ["GOOGLE_TABLE"]
    return f"{dataset}.{table}"


def _qualify_default_table(sql_query: str) -> str:
    """Add the fully-qualified default table name to bare references.

    Args:
        sql_query: Original SQL text that may contain unqualified default table references.

    Returns:
        SQL string with the default table rewritten as ``dataset.table`` (wrapped in backticks).
    """
    table = os.environ["GOOGLE_TABLE"]
    full_name = f"`{get_default_table_fqn()}`"
    dataset = os.environ["GOOGLE_DATASET"]
    pattern_table = re.compile(rf"(?<![\w.]){re.escape(table)}(?![\w.])", re.IGNORECASE)
    qualified_sql = pattern_table.sub(full_name, sql_query)
    pattern_dataset = re.compile(rf"`?{re.escape(dataset)}\.{re.escape(table)}`?", re.IGNORECASE)
    qualified_sql = pattern_dataset.sub(full_name, qualified_sql)
    return qualified_sql


def generate_sql(
    prompt: str,
    normalized_prompt: Optional[str] = None,
    *,
    limit: Optional[int] = None,
) -> str:
    """Deprecated helper retained for backward compatibility."""
    _ = limit if limit is not None else get_forced_sql_limit()
    raise NotImplementedError(
        "generate_sql is deprecated. Inline the SQL within the generated analysis code."
    )


@lru_cache(maxsize=1)
def _get_bigquery_client() -> bigquery.Client:
    """Instantiate (and cache) a BigQuery client configured via environment variables.

    Returns:
        google.cloud.bigquery.Client: Client connected to the configured project.
    """
    project_id = os.environ["GOOGLE_PROJECT_ID"]
    adc_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    logger.info("Creating BigQuery client for project %s", project_id)
    credentials = service_account.Credentials.from_service_account_file(adc_file)
    connection_info = {"project_id": project_id, "credentials": credentials}
    return make_bq_client(connection_info)


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Execute SQL against BigQuery and return the result as a DataFrame.

    Args:
        sql_query: Fully-rendered SQL text to execute.

    Returns:
        pd.DataFrame: Query results converted via ``to_dataframe``.

    Raises:
        google.api_core.exceptions.BadRequest: When BigQuery reports a query error
            that cannot be auto-corrected (e.g., malformed SQL).
    """
    client = _get_bigquery_client()
    logger.info("Executing SQL query")
    job_config = bigquery.QueryJobConfig(use_legacy_sql=False)
    current_sql = sql_query
    attempted_fix = False

    while True:
        try:
            job = client.query(current_sql, job_config=job_config)
            df = job.to_dataframe()
            logger.info("Query returned %s rows and %s columns", df.shape[0], df.shape[1])
            return df
        except BadRequest as exc:
            message = str(exc)
            if not attempted_fix and "must be qualified with a dataset" in message:
                attempted_fix = True
                current_sql = _qualify_default_table(current_sql)
                logger.warning("Retrying query with fully qualified default table")
                continue
            raise


def upload_file_to_s3(local_path: str, *, content_type: Optional[str] = None) -> str:
    """Upload a local file to S3 and return its HTTPS location.

    Args:
        local_path: Filesystem path to the file to upload.
        content_type: Optional MIME type to set on the uploaded object.

    Returns:
        HTTPS URL pointing to the uploaded object.

    Raises:
        FileNotFoundError: When ``local_path`` does not exist.
        RuntimeError: When the S3 upload fails for any reason.
    """
    bucket_name = os.environ["AWS_S3_BUCKET"]
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    local_path_obj = Path(local_path)
    if not local_path_obj.is_file():
        raise FileNotFoundError(f"Image path not found: {local_path}")

    key = local_path_obj.name
    extra_args = {"ContentType": content_type} if content_type else None

    client = boto3.client("s3")
    try:
        logger.info("Uploading %s to bucket %s", local_path, bucket_name)
        if extra_args:
            client.upload_file(str(local_path_obj), bucket_name, key, ExtraArgs=extra_args)
        else:
            client.upload_file(str(local_path_obj), bucket_name, key)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to upload {local_path} to s3://{bucket_name}/{key}: {exc}")

    logger.info("Uploaded to s3://%s/%s", bucket_name, key)
    return f"https://s3.{region}.amazonaws.com/{bucket_name}/{key}"


__all__ = [
    "REQUIRED_ENV_VARS",
    "normalize_prompt",
    "generate_sql",
    "execute_sql_query",
    "upload_file_to_s3",
    "get_default_table_fqn",
    "check_required_env_vars",
    "MissingEnvironmentVariableError",
]
