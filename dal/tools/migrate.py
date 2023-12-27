"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
   
   this tool will migrate all the data from the old scopes to the new models
    inside Redis. It will also validate the data and save it if it is valid.
"""
#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
import logging
from threading import Lock
from tqdm import tqdm
import sys

from dal.movaidb import Redis
import dal.new_models
import dal.scopes
from dal.scopes.robot import Robot

import movai_core_enterprise.scopes
import movai_core_enterprise.new_models

logger = logging.getLogger("migrate.tool")
handler = logging.FileHandler("/opt/mov.ai/app/migrate.log")
handler.setLevel(logging.INFO)
logger.addHandler(handler)
dal_models = (
    "Application",
    "Callback",
    "Configuration",
    "get_project_ids",
    "Flow",
    "Message",
    "MovaiBaseModel",
    "Node",
    "Ports",
    "System"
)
enterprise_models = ("Annotation",)
pydantic_models = set()
pydantic_models.update(dal_models)
pydantic_models.update(enterprise_models)


db = sys.argv[1] if len(sys.argv) > 1 else "global"
logger.info(f"migrating db: {db}")
objs = set()
count = {}
bars = {}
lock = Lock()
database = Redis().db_global if db == "global" else Redis().db_local
scopes_keys = [key.decode() for key in database.keys("*")]


def class_exist(name):
    try:
        getattr(dal.new_models, name)
        return True
    except AttributeError:
        try:
            getattr(movai_core_enterprise.new_models, name)
            return True
        except AttributeError:
            return False


def validate_model(model, id):
    global bars, objs

    try:
        scopes_class = getattr(dal.scopes, model)
        pydantic_class = getattr(dal.new_models, model)
    except AttributeError:
        scopes_class = getattr(movai_core_enterprise.scopes, model)
        pydantic_class = getattr(movai_core_enterprise.new_models, model)

    try:
        if scopes_class is Robot:
            obj_dict = scopes_class().get_dict()
        else:
            obj_dict = scopes_class(id).get_dict()
        obj = pydantic_class.model_validate(obj_dict)
        obj.save()
        with lock:
            bars[model].update(1)
    except Exception as exc:
        logger.error(exc)
        with lock:
            bars[model].write(f"Validation Error for {model} :: {id}")
        pass


def chunk_data(data, n):
    """Divide the data into n chunks."""
    data = list(data)
    if len(data) < n:
        return [[x] for x in data]
    chunk_size = len(data) // n
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


invalid_models = set()
valid_models = set()
ignoring = list()
for key in scopes_keys:
    if "," in key:
        model, id, *_ = key.split(":")
        id = id.split(",")[0]
        if model not in pydantic_models:
            continue
        if not class_exist(model):
            if f"{model},{id}" not in ignoring:
                logger.info("Could not find %s in new_models, ignoring %s::%s", model, model, id)
                ignoring.append(f"{model},{id}")
            invalid_models.add(model)
            continue
        valid_models.add(model)
        objs.add((model, id))
        if model not in count:
            count[model] = set()
        count[model].add(id)


pos = 0
for model in valid_models:
    bars[model] = tqdm(total=len(count[model]), desc=f"{model} Files", position=pos)
    pos += 1

# Number of threads you'd like to use
NUM_THREADS = 8
# list of lists containing the data to be processed
chunks = chunk_data(objs, NUM_THREADS)

for chunk in chunks:
    for model, id in chunk:
        validate_model(model, id)

with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [
        executor.submit(validate_model, model, id) for chunk in chunks for model, id in chunk
    ]

    for future in futures:
        future.result()  # to capture any exceptions thrown inside threads
