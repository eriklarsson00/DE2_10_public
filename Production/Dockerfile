FROM ubuntu:20.04
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y python3-pip
WORKDIR /app/
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["./app.py","--host=0.0.0.0"]
