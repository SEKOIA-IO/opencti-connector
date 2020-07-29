FROM python:3.8-alpine

COPY requirements.txt /opt/requirements.txt

# Install Python modules
# hadolint ignore=DL3003
RUN apk --no-cache add git build-base libmagic && \
    cd /opt && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del git build-base && \
    rm requirements.txt

# Copy the connector
COPY src /opt/opencti-connector-sekoia

# Expose and entrypoint
WORKDIR /opt/opencti-connector-sekoia
ENTRYPOINT ["python3", "sekoia.py"]
