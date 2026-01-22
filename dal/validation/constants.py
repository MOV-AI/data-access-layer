"""Validation constants"""
from os.path import dirname, realpath


dir = dirname(realpath(__file__))
REDIS_SCHEMA_FOLDER_PATH = f"file://{dir}/redis_schema"
JSON_SCHEMA_FOLDER_PATH = f"file://{dir}/json_schema"
