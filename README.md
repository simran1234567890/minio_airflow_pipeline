#  Event-Driven Data Pipeline with MinIO, Airflow, and Webhook

This project implements an event-driven data pipeline that automatically compresses files uploaded to MinIO using Airflow DAGs triggered by webhook events.

##  Architecture Overview

```
File Upload → MinIO → Webhook → Airflow DAG → Compression → Email Notification
```

### Components:
- **MinIO**: Object storage for file uploads
- **Webhook Server**: Flask app that receives MinIO events and triggers Airflow DAGs
- **Airflow**: Orchestrates the compression workflow
- **Email Service**: Sends notifications with compression metadata

##  Project Structure

```
Airflow-event-driven/
├── dags/
│   └── file_compress.py         # Airflow DAG for file compression
├── webhook/
│   ├── app.py                   # Flask webhook server
│   ├── Dockerfile               # Webhook container setup
│   └── requirements.txt         # Python dependencies
├── docker-compose.yml           # Main orchestration file
├── setup.sh                     # Automated setup script
└── README.md                    # This file
```

##  Quick Start

### 1. Launch Services

```bash
# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

Or manually:
```bash
# Start all services
docker-compose up --build -d

# Wait for services to be ready (30-60 seconds)
sleep 45
```

### 2. Create MinIO Buckets

```bash
# Install MinIO Client (mc)
# macOS: brew install minio/stable/mc
# Linux: wget https://dl.min.io/client/mc/release/linux-amd64/mc

# Configure MinIO client
mc alias set local http://localhost:9000 minioadmin minioadmin

# Create buckets
mc mb local/testing-files
mc mb local/compressed-files
```

### 3. Configure MinIO Notifications (Optional)

```bash
# Add webhook notification for file uploads
mc event add local/testing-files arn:minio:sqs::webhook:webhook --event put
```

##  Service URLs & Credentials

| Service | URL | Credentials |
|---------|-----|-------------|
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **MinIO API** | http://localhost:9000 | `minioadmin` / `minioadmin` |
| **Airflow** | http://localhost:8080 | `airflow` / `airflow` |
| **Webhook** | http://localhost:5000 | No authentication |

## Workflow Details

### 1. File Upload Trigger
When a file is uploaded to the `testing-files` bucket in MinIO:
- MinIO sends a webhook event to the Flask server
- The webhook server extracts the file information
- It triggers the Airflow DAG `minio_file_compressor`

### 2. Airflow DAG Process
The DAG performs these steps:
1. **Download**: Retrieves the file from MinIO `testing-files` bucket
2. **Compress**: Uses gzip to compress the file
3. **Upload**: Stores the compressed file in `compressed-files` bucket
4. **Notify**: Sends email to `simranpandey107@gmail.com` with metadata
5. **Cleanup**: Removes temporary files

### 3. Email Notification
The email includes:
- Original file name and size
- Compressed file name and size
- Compression ratio and space saved
- Timestamp of completion

##  Testing

### 1. Test Webhook Server
```bash
curl http://localhost:5000/test
```

### 2. Manual DAG Trigger
```bash
curl -X POST http://localhost:5000/trigger-dag \
  -H 'Content-Type: application/json' \
  -d '{"object_name":"test.txt"}'
```

### 3. Upload Test File
```bash
# Create a test file
echo "This is a test file for compression" > test.txt

# Upload to MinIO
mc cp test.txt local/testing-files/
```

### 4. Check Results
- **Compressed file**: Check `compressed-files` bucket in MinIO console
- **DAG runs**: Check Airflow UI at http://localhost:8080
- **Email**: Check your inbox for compression notification

##  Monitoring & Debugging

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs webhook
docker-compose logs airflow-webserver
docker-compose logs minio
```

### Check Service Health
```bash
# MinIO
curl http://localhost:9000/minio/health/live

# Airflow
curl http://localhost:8080/health

# Webhook
curl http://localhost:5000/health
```

##  Configuration

### Environment Variables
The webhook server uses these environment variables:
- `AIRFLOW_API_URL`: Airflow API endpoint (default: http://airflow-webserver:8080)
- `AIRFLOW_USERNAME`: Airflow username (default: airflow)
- `AIRFLOW_PASSWORD`: Airflow password (default: airflow)

### Email Configuration
To enable actual email sending, modify the `send_email_notification` function in `dags/file_compress.py`:

```python
# Uncomment and configure SMTP settings
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, "your_app_password")
text = msg.as_string()
server.sendmail(sender_email, recipient_email, text)
server.quit()
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

2. **DAG not triggering**
   - Check webhook logs: `docker-compose logs webhook`
   - Verify Airflow is running: `curl http://localhost:8080/health`
   - Test manual trigger: `curl -X POST http://localhost:5000/trigger-dag -H 'Content-Type: application/json' -d '{"object_name":"test.txt"}'`

3. **File compression failing**
   - Check DAG logs in Airflow UI
   - Verify MinIO buckets exist
   - Check file permissions

4. **Email not sending**
   - Email notifications are currently logged to console
   - Configure SMTP settings for actual email delivery

### Reset Everything
```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
./setup.sh
```

##  Scaling Considerations

- **Multiple Workers**: Add more Airflow workers in `docker-compose.yml`
- **Load Balancing**: Use nginx for webhook load balancing
- **Persistence**: Mount MinIO data to host volumes
- **Monitoring**: Add Prometheus/Grafana for metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

This project is open source and available under the MIT License. 
