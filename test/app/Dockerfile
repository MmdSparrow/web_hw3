FROM python:3.9-slim

WORKDIR /app

# Copy application code and requirements
COPY producer.py requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Run the producer script
CMD ["python", "producer.py"]
