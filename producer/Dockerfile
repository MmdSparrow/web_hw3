FROM python:3.9-slim
WORKDIR /app
COPY producer.py ../requirements.txt ./
RUN pip install -r requirements.txt
CMD ["python", "producer.py"]