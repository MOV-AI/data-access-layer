# data-access-layer
The data access layer (DAL) is an abstraction layer for accessing the required data. 
The data may be fetched/written (pending permission) from/to the appropriate data sources:
    GIT
    DB (Redis)
    File system 
    
The Data Service provides:
    1) Validation of user permissions before accessing the data
    2) Enforcing the appropriate JSON schema when writing data
    3) Validating compatibility between a document versions

## Usage
The DAL exposes API for reading and writing the data and is used by the MOV.AI platform component
The DAL is a python package and it is incapsulated in the Backend and in the Spawner (Flow initiator) containers

> Prerequisites : The flow initiator is depended on 2 packages:
    1) jsonschema
    2) gitpython
    3) py3rosmsgs
    4) aioredis
    5) redis
    6) pyros-genmsg


## Build

The complete build process:
- a python module building step which will create a `.whl` file


## build pip module

    rm dist/*
    python3 -m build .

## install pip module locally

    python3 -m venv .testenv
    source .testenv/bin/activate
    python3 -m pip install --no-cache-dir \
    --index-url="https://artifacts.cloud.mov.ai/repository/pypi-experimental/simple" \
    --extra-index-url https://pypi.org/simple \
    ./dist/*.whl

