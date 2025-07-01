# Data Access Layer
The Data Access Layer (DAL) is an abstraction layer Library for accessing data.
The data may be read/written (pending permission) from/to the followin data sources:
- GIT
- DB (Redis)
- File system

The Data Service provides:
1. Validation of user permissions before accessing the data
2. Enforcing the appropriate JSON schema when writing data
3. Validating compatibility between a document versions

## Usage

The DAL exposes APIs for reading and writing the data and is used by MOV.AI platform components.
It's a python package by message-server, backend and flow-initiator services.

### Versioning

| EE     | DAL branch      | DAL version |
|--------|-----------------|-------------|
| 2.4.1  | releases/3.1    | 3.1.x.y     |
| 2.4.4  | releases/3.2    | 3.2.x.y     |
| 2.5.0  | main            | 3.3.x.y     |

## Development

### Build

To build DAL run `make build`

### Install locally

    python3 -m venv .testenv
    source .testenv/bin/activate
    python3 -m pip install --no-cache-dir \
    --index-url="https://artifacts.cloud.mov.ai/repository/pypi-experimental/simple" \
    --extra-index-url https://pypi.org/simple \
    ./dist/*.whl
