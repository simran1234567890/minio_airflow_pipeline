# Quick Start Guide

## 1. Start the Pipeline

```bash
# Start all services
docker-compose up --build -d

# Wait for services to be ready (45-60 seconds)
sleep 45
```

## 2. Create MinIO Buckets

```bash
# Install MinIO Client (if not installed)
# macOS: brew install minio/stable/mc
# Linux: wget https://dl.min.io/client/mc/release/linux-amd64/mc

# Configure and create buckets
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/testing-files
mc mb local/compressed-files
```

## 3. Test the Pipeline

```bash
# Run the test script
./test_pipeline.sh

# Or test manually:
# 1. Test webhook
curl http://localhost:5000/test

# 2. Upload a test file
echo "Hello World" > test.txt
mc cp test.txt local/testing-files/

# 3. Check results
mc ls local/compressed-files/
```

## 4. Access Services

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Webhook**: http://localhost:5000

## 5. Monitor the Process

1. Upload a file to `testing-files` bucket
2. Check Airflow UI for DAG runs
3. Find compressed file in `compressed-files` bucket
4. Check logs for email notifications

## Troubleshooting

```bash
# View logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up --build -d

# Check service health
curl http://localhost:9000/minio/health/live
curl http://localhost:8080/health
curl http://localhost:5000/health
``` 
