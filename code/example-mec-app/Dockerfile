FROM python:3.9-slim-buster
WORKDIR /example-mec-app/
COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT python3 ./mec_sandbox_data_collector.py
