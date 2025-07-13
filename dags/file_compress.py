import os
import gzip
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.models import Variable
import shutil

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# MinIO configuration
MINIO_ENDPOINT = 'http://minio:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
SOURCE_BUCKET = 'testing-files'
DEST_BUCKET = 'compressed-files'

def compress_file_from_minio(**context):
    object_name = context['dag_run'].conf.get('object_name')
    print(f"[INFO] Received object name: {object_name}")
    
    if not object_name:
        raise ValueError("Missing 'object_name' in dag_run.conf")

    local_input_path = f"/tmp/{object_name}"
    local_output_path = f"{local_input_path}.gz"
    compressed_key = f"{os.path.basename(object_name)}.gz"

    print(f"[INFO] Downloading from: {SOURCE_BUCKET}/{object_name}")
    print(f"[INFO] Local input path: {local_input_path}")
    print(f"[INFO] Local output path: {local_output_path}")
    print(f"[INFO] Compressed key: {compressed_key}")

    os.makedirs(os.path.dirname(local_input_path), exist_ok=True)

    s3 = boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )

    print(f"[INFO] Downloading file from MinIO...")
    s3.download_file(SOURCE_BUCKET, object_name, local_input_path)
    original_size = os.path.getsize(local_input_path)
    print(f"[INFO] Downloaded file size: {original_size} bytes")

    print(f"[INFO] Compressing file...")
    with open(local_input_path, 'rb') as f_in, gzip.open(local_output_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    compressed_size = os.path.getsize(local_output_path)
    print(f"[INFO] Compressed file size: {compressed_size} bytes")
    print(f"[INFO] Compression ratio: {original_size/compressed_size:.2f}x")
    
    print(f"[INFO] Uploading compressed file to {DEST_BUCKET}/{compressed_key}")
    s3.upload_file(local_output_path, DEST_BUCKET, compressed_key)
    print(f"[INFO] Upload complete!")

    context['ti'].xcom_push(key='object_name', value=object_name)
    context['ti'].xcom_push(key='original_size', value=original_size)
    context['ti'].xcom_push(key='compressed_size', value=compressed_size)

    os.remove(local_input_path)
    os.remove(local_output_path)
    print(f"[INFO] Cleanup complete - temporary files removed")

# Create the DAG
dag = DAG(
    dag_id="minio_file_compressorone",
    description="Compress uploaded file from MinIO and upload back",
    default_args=default_args,
    schedule_interval=None,
    tags=["minio", "compression"],
    catchup=False,
)

# Define the task
compress_task = PythonOperator(
    task_id="compress_and_reupload",
    python_callable=compress_file_from_minio,
    provide_context=True,
    dag=dag
)

send_email = EmailOperator(
    task_id="email_send",
    to='simranpandey107@gmail.com',
    subject='Airflow File Compression Complete',
    html_content="""
        <h3>File Compression Complete</h3>
        <p><strong>Original File:</strong> {{ ti.xcom_pull(task_ids='compress_and_reupload', key='object_name') }}</p>
        <p><strong>Original Size:</strong> {{ ti.xcom_pull(task_ids='compress_and_reupload', key='original_size') }} bytes</p>
        <p><strong>Compressed Size:</strong> {{ ti.xcom_pull(task_ids='compress_and_reupload', key='compressed_size') }} bytes</p>
    """,
    dag=dag
)

compress_task >> send_email 