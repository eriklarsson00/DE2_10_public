FROM ubuntu:20.04
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y python3-pip
WORKDIR /app/
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install ray[tune]
EXPOSE 6379 6380 12345
# CMD ["python", "train_models.py"]