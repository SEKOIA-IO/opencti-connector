# opencti-connector

This repository contains the SEKOIA.IO connector for OpenCTI.

## Installation

To install the connector you can follow the official [OpenCTI connectors documentation](https://www.notion.so/Connectors-4586c588462d4a1fb5e661f2d9837db8
). 

## Docker images

The docker images of the project can be found at https://github.com/orgs/SEKOIA-IO/packages?tab=packages&q=opencti-connector

To pull an image one the following commands should be used:

```bash
$ docker pull ghcr.io/sekoia-io/opencti-connector:latest
$ docker pull ghcr.io/sekoia-io/opencti-connector:4
```

To use the connector with the old 3.x version of OpenCTI the `3[.x[.x]]` tags must be used when pulling the image:

```bash
$ docker pull ghcr.io/sekoia-io/opencti-connector:3
$ docker pull ghcr.io/sekoia-io/opencti-connector:3.3
$ docker pull ghcr.io/sekoia-io/opencti-connector:3.3.2
```


## Specific parameters

Here are the parameters specific to the sekoia connector:

* `api_key`: The API key to access the SEKOIA API, **required**.
* `base_url`: The SEKOIA API base url, *optional*.
* `collection`: The SEKOIA collections to use, *optional*

Those parameters are located under the `sekoia` category in the config file or are prefixed by `SEKOIA_` in the docker compose environment parameters.

Example in the `config.yml` file:

```yml
sekoia:
  api_key: 'ChangeMe'  # Mandatory
  base_url: 'https://api.sekoia.io'  # Optional
  collection: 'd6092c37-d8d7-45c3-8aff-c4dc26030608'  # Optional
```

Example in the `docker-compose.yml` file:

```yaml
connector-sekoia:
    environment:
      ...
      - SEKOIA_API_KEY=ChangeMe  # Mandatory
      - SEKOIA_BASE_URL='https://api.sekoia.io'  # Optional
      - SEKOIA_COLLECTION='d6092c37-d8d7-45c3-8aff-c4dc26030608'  # Optional
```

## Examples

### Docker compose

Here's a an example of the docker compose part that could be added to your main file to add the SEKOIA connector to the stack:

```yaml
  connector-sekoia:
    image: ghcr.io/sekoia-io/opencti-connector:latest
    environment:
      - OPENCTI_URL=http://localhost:8080
      - OPENCTI_TOKEN=ChangeMe
      - CONNECTOR_ID=ChangeMe
      - CONNECTOR_TYPE=EXTERNAL_IMPORT
      - CONNECTOR_NAME=SEKOIA.IO
      - CONNECTOR_SCOPE=identity,attack-pattern,course-of-action,intrusion-set,malware,tool,report,location,vulnerability,indicator
      - CONNECTOR_CONFIDENCE_LEVEL=3
      - CONNECTOR_UPDATE_EXISTING_DATA=true
      - CONNECTOR_LOG_LEVEL=info
      - SEKOIA_API_KEY=ChangeMe
    restart: always
```

### Config file

An example of the config file `config.yml` can be found in [src/config.yml.sample](src/config.yml.sample).
