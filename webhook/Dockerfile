FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN pip install flask requests

# Copy application code
COPY app.py .

# Expose port
EXPOSE 5000

# Ensure unbuffered output for Python
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"] 