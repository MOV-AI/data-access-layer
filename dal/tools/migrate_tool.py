#!/usr/bin/env python3
"""this tool will migrate all the data from the old scopes to the new models
    inside Redis. It will also validate the data and save it if it is valid.
"""
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import logging
from threading import Lock
from typing import Any

from argparse import ArgumentParser
from pydantic import ValidationError
from tqdm import tqdm

from movai_core_shared.core.base_command import BaseCommand

from dal.movaidb import Redis
from dal.new_models import PYDANTIC_MODELS
import dal.new_models
import dal.scopes
from dal.scopes.system import System

try:
    import movai_core_enterprise.scopes
    import movai_core_enterprise.new_models
except ImportError:
    pass


def model_exist(model_type: str) -> bool:
    """Checks if a model exist in the new format.

    Args:
        model_type (str): The name of the model to check.

    Returns:
        bool: True if exist, False otherwise.
    """
    try:
        getattr(dal.new_models, model_type)
        return True
    except AttributeError:
        try:
            getattr(movai_core_enterprise.new_models, model_type)
            return True
        except AttributeError:
            return False


class MigrationCommands(BaseCommand):
    """Base class for migration tool operations."""

    def __init__(self, subparsers, **kwargs) -> None:
        super().__init__(**kwargs)
        file_handler = logging.FileHandler("migrate.log")
        file_handler.setLevel(logging.DEBUG)
        self.log.addHandler(file_handler)
        self.define_arguments(subparsers)
        self.objects = {}
        self.progress_bars = {}
        self.model_count = {}

    def parse_db(self, **kwargs) -> None:
        db_scope = kwargs.get("db_scope")
        db_id = kwargs.get("db_id")
        db = Redis(db_id).db_global if db_scope == "global" else Redis(db_id).db_local
        return db

    def load_keys(self) -> None:
        db_keys = [key.decode() for key in self.db.keys()]
        return db_keys

    def parse_model(self, **kwargs):
        models_to_convert = set(kwargs.get("convert"))
        models_to_ignore = set(kwargs.get("ignore"))

        for model in models_to_convert:
            if model not in PYDANTIC_MODELS:
                models_to_ignore.add(model)
                self.log.warning(f"The model: {model} can not be converted to pydantic format.")

        for model in models_to_ignore:
            if model in models_to_convert:
                models_to_convert.remove(model)

        self.log.info(f"The following models will be converted after scan: {models_to_convert}")
        self.log.info(f"The follogin models will be ignored after scan: {models_to_ignore}")

        return models_to_convert


class Convert(MigrationCommands):
    """A class for migrating objects from old format to new format (pydantic)"""

    def __init__(self, subparsers, **kwargs) -> None:
        super().__init__(subparsers, **kwargs)
        self.invalid_models = {}
        self.valid_models = {}

    @classmethod
    def define_arguments(cls, subparsers) -> None:
        """An abstract function for implementing command arguments.

        Args:
            subparsers (_type_): _description_
        """
        parser: ArgumentParser = subparsers.add_parser(
            "convert", help="converts an object from old movai format to pydantic format"
        )
        parser.add_argument(
            "-s", "--db-scope", help="the type of db to use", nargs="?", default="global"
        )
        parser.add_argument("-d", "--db-id", help="the id of the db to use", nargs="?", default=0)
        parser.add_argument(
            "-c",
            "--convert",
            help="a list of models to convert",
            nargs="*",
            default=PYDANTIC_MODELS
        )
        parser.add_argument(
            "-i",
            "--ignore",
            help="a list of models to ignore while converting",
            nargs="*",
            default=[],
        )

    def execute(self, **kwargs) -> None:
        """Executes the relevant command."""
        self.db = self.parse_db(**kwargs)
        self.models_to_convert = self.parse_model(**kwargs)
        self.keys = self.load_keys()
        self.scan()
        self.init_processs_bars()
        for model_type, models_ids in self.valid_models.items():
            for model_id in models_ids:
                self.convert_model(model_type, model_id)
        # with ThreadPoolExecutor(len(self.valid_models)) as executor:
        #    futures = [executor.submit(self.convert_model, model, id) for model, id in self.objects]

    #
    # for future in futures:
    #    future.result()  # to capture any exceptions thrown inside threads

    def convert_model(self, model_type: str, model_name: str):
        """_summary_

        Args:
            model_type (Any): _description_
            id (str): _description_
        """

        try:
            scopes_class = getattr(dal.scopes, model_type)
            pydantic_class = getattr(dal.new_models, model_type)
        except AttributeError:
            scopes_class = getattr(movai_core_enterprise.scopes, model_type)
            pydantic_class = getattr(movai_core_enterprise.new_models, model_type)
        try:
            if scopes_class is System:
                obj_dict = scopes_class(id).get_dict()
            else:
                obj_dict = scopes_class(model_name).get_dict()
            obj = pydantic_class(**obj_dict)
            obj.save()
            # self.log.info(
            #    f"Successfully converted the object {model_type}:{model_name} to pydantic format.")
            self.progress_bars[model_type].update(1)
        except ValidationError as verr:
            self.log.error(
               f"Got Validation error, while trying to convert object {model_type}:{model_name}"
            )
            self.log.error(verr)
        except Exception as exc:
            self.log.error(
               f"Got the following error: {exc} while trying to convert the object {model_type}::{model_name}"
            )
            

    def scan(self):
        """Scans the db for keys and filter only the required objects."""
        for key in self.keys:
            if "," not in key:
                continue
            model_type, model_id, *_ = key.split(":")
            model_id = model_id.split(",")[0]
            if model_type not in self.models_to_convert:
                continue
            if not model_exist(model_type):
                self.logger.info(
                    f"Could not find {model_type} in new_models, ignoring {model_type}::{model_id}"
                )
                if model_type not in self.invalid_models:
                    self.invalid_models[model_type] = set()
                self.invalid_models[model_type].add(model_id)
                continue
            if model_type not in self.valid_models:
                self.valid_models[model_type] = set()
            self.valid_models[model_type].add(model_id)

    def init_processs_bars(self):
        """Initialize the Tqdm object for displaying progress bars."""
        pos = 0
        for model, names in self.valid_models.items():
            self.progress_bars[model] = tqdm(
                total=len(names), desc=f"{model} objects", position=pos
            )
            pos += 1


class Restore(MigrationCommands):
    "Restore operations"

    @classmethod
    def define_arguments(cls, subparsers) -> None:
        """An abstract function for implementing command arguments.

        Args:
            subparsers (_type_): _description_
        """
        parser = subparsers.add_parser(
            "restore", help="restores an object from pydantic format to old movai format"
        )
        parser.add_argument("-m", "--model", help="a model to convert", required=True)
        parser.add_argument("-n", "--name", help="The name of the object to convert")
        parser.add_argument("-i", "--ignore", help="a model to ignore while converting")

    def execute(self, **kwargs) -> None:
        """Executes the relevant command."""
        pass


class Commander:
    """a class for launching tool sub commands"""

    def __init__(self, subparsers) -> None:
        """Ctor

        Args:
            subparsers (_type_): A subparser for adding sub commands.
        """
        self._commands = {}
        self.register_command(Convert(subparsers))
        # self.register_command(Restore(subparsers))

    def register_command(self, command: BaseCommand):
        """Register the command in dictionary for easy launch by commander.

        Args:
            command (BaseCommand): A command which implement 'execute' function.
        """
        self._commands[command.name] = command

    def run(self, **kwargs):
        """runs the command."""
        command = kwargs.pop("command")
        self._commands[command].safe_execute(**kwargs)


def main():
    tool_description = """The migrate tool is a script for converting core objects to pydantic implementation.
    It is currently supports the following commands: convert and restore."""
    parser = ArgumentParser(description=tool_description, prog="migrate_tool.py")
    subparsers = parser.add_subparsers(dest="command")
    commander = Commander(subparsers)
    args = parser.parse_args()
    kwargs = dict(args._get_kwargs())
    commander.run(**kwargs)


if __name__ == "__main__":
    main()
