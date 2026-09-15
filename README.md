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
4. Static analysis of the metadata installed in a project - see [dal/validation/README.md](./dal/validation/README.md) for documentation of every issue that can be reported, its severity and when it is triggered.

## Usage

The DAL exposes APIs for reading and writing the data and is used by MOV.AI platform components.
It's a python package by message-server, backend and flow-initiator services.

### Versioning

| EE     | DAL branch      | DAL version |
|--------|-----------------|-------------|
| 2.4.1  | releases/3.1    | 3.1.x.y     |
| 2.4.4  | releases/3.2    | 3.2.x.y     |
| 2.5.1  | releases/3.23   | 3.23.x.y    |
| 3.0.0  | releases/3.28   | -           |
| 3.0.1  | main            | -           |

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
