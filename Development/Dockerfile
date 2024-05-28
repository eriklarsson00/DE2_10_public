FROM python:3.9-slim
WORKDIR /app/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install ray[tune]
EXPOSE 6379 6380 12345
CMD ["python", "train_models.py"]