import requests
import json
from flask import Flask, request
from requests.auth import HTTPBasicAuth
import base64

app = Flask(__name__)

AIRFLOW_TRIGGER_URL = "http://airflow-webserver:8080/api/v1/dags/minio_file_compressorone/dagRuns"
AIRFLOW_USERNAME = "admin"
AIRFLOW_PASSWORD = "admin"

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}, 200

@app.route("/", methods=["POST"])
def index():
    print("Raw request data:", request.data)
    try:
        data = request.get_json(force=True)
        print("=" * 50)
        print("📨 MINIO EVENT RECEIVED")
        print("=" * 50)
        print("Received S3 event:", json.dumps(data, indent=2))
        
        # Defensive extraction of object_name
        object_name = None
        try:
            object_name = data["Records"][0]["s3"]["object"]["key"]
            bucket_name = data["Records"][0]["s3"]["bucket"]["name"]
            print(f"📁 Object: {object_name}")
            print(f"🪣 Bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Could not extract object_name: {e}")
            print(f"Event structure: {data}")
        
        if object_name:
            # Trigger Airflow DAG
            dag_config = {"conf": {"object_name": object_name}}
            print(f"🚀 Triggering DAG with config: {json.dumps(dag_config, indent=2)}")
            print(f"[DEBUG] Using credentials: {AIRFLOW_USERNAME}/{AIRFLOW_PASSWORD}")
            print(f"[DEBUG] Auth type: HTTPBasicAuth")
            # Preemptive Basic Auth workaround
            userpass = f"{AIRFLOW_USERNAME}:{AIRFLOW_PASSWORD}".encode("utf-8")
            b64userpass = base64.b64encode(userpass).decode("utf-8")
            headers = {
                "Accept": "application/json",
                "Authorization": f"Basic {b64userpass}"
            }
            response = requests.post(
                AIRFLOW_TRIGGER_URL,
                json=dag_config,
                headers=headers
            )
            print(f"[DEBUG] Airflow API response status: {response.status_code}")
            print(f"[DEBUG] Airflow API response body: {response.text}")
            print(f" DAG Trigger Response: {response.status_code} - {response.text}")
            if response.status_code == 200:
                print("Successfully triggered Airflow DAG!")
            else:
                print(f" Failed to trigger DAG: {response.status_code}")
        else:
            print(" object_name is missing, not triggering DAG.")
        
    except Exception as e:
        print(f" Unexpected error: {e}")
    print("=" * 50)
    return "", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 