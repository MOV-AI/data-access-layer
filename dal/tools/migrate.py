"""this tool will migrate all the data from the old scopes to the new models
    inside Redis. It will also validate the data and save it if it is valid.
"""
from concurrent.futures import ThreadPoolExecutor
from dal.movaidb import Redis
import dal.scopes
import movai_core_enterprise.scopes
import movai_core_enterprise.new_models
import dal.new_models
from tqdm import tqdm
from threading import Lock
import sys
import logging

logger = logging.getLogger("migrate.tool")
handler = logging.FileHandler("migrate.log")
handler.setLevel(logging.INFO)
logger.addHandler(handler)


db = sys.argv[1] if len(sys.argv) > 1 else "global"
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
        obj = pydantic_class.model_validate(scopes_class(id).get_dict())
        obj.save()
        with lock:
            bars[model].update(1)
    except Exception:
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
        type, id, *_ = key.split(":")
        id = id.split(",")[0]
        if not class_exist(type):
            if f"{type},{id}" not in ignoring:
                logger.info("Could not find %s in new_models, ignoring %s::%s", type, type, id)
                ignoring.append(f"{type},{id}")
            invalid_models.add(type)
            continue
        valid_models.add(type)
        objs.add((type, id))
        if type not in count:
            count[type] = set()
        count[type].add(id)


pos = 0
for model in valid_models:
    bars[model] = tqdm(total=len(count[model]), desc=f"{model} Files", position=pos)
    pos += 1

# Number of threads you'd like to use
NUM_THREADS = 8
# list of lists containing the data to be processed
chunks = chunk_data(objs, NUM_THREADS)


with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [
        executor.submit(validate_model, model, id) for chunk in chunks for model, id in chunk
    ]

    for future in futures:
        future.result()  # to capture any exceptions thrown inside threads
