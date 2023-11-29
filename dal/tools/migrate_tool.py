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

from movai_core_shared.logger import Log
from movai_core_shared.core.base_command import BaseCommand

from dal.movaidb import Redis
import dal.new_models
import dal.scopes

import movai_core_enterprise.scopes
import movai_core_enterprise.new_models

from tqdm import tqdm

NUM_THREADS = 8
PYDANTIC_SUPPORTED_MODELS = (
    "Flow",
    "Callback",
    "Node",
    "Configuration",
    "Application",
    "Message",
    "Package",
    "Ports",
    "Robot",
    "Role",
    "System"
)


def convert_list_to_dict(arg_list: list) -> dict:
    arguments = {}
    for arg in arg_list:
        if isinstance(arg, tuple):
            if len(arg) > 1:
                arg_key = arg[0]
                arg_val = arg[1]
                if arg_val is None:
                    continue
                if isinstance(arg_val, list):
                    arg_val = parse_tags(arg_val)
                arguments[arg_key] = arg_val
            else:
                arguments[arg[0]] = ""
    return arguments

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
    """Base class for migration tool operations.
    """
    def __init__(self, subparsers, **kwargs) -> None:
        super().__init__(**kwargs)
        file_handler = logging.FileHandler("migrate.log")
        file_handler.setLevel(logging.DEBUG)
        self.log.addHandler(file_handler)
        self.define_arguments(subparsers)
        self.objects = {}
        self.db = self.parse_db()

    def parse_db(self, **kwargs) -> None:
        db_scope = kwargs.get("db-scope")
        db_id = kwargs.get("db-id")
        db = Redis(db_id).db_global if db_scope == "global" else Redis(db_id).db_local
        return db

    def load_keys(self) -> None:
        db_keys = [key.decode() for key in self.db.keys()]
        return db_keys


class Convert(MigrationCommands):
    """A class for migrating objects from old format to new format (pydantic)
    """

    def __init__(self, subparsers, **kwargs) -> None:
        super().__init__(subparsers, **kwargs)
        self.models_to_convert = self.parse_model(kwargs)
        self.keys = self.load_keys()

    @classmethod
    def define_arguments(cls, subparsers) -> None:
        """An abstract function for implementing command arguments.

        Args:
            subparsers (_type_): _description_
        """
        parser: ArgumentParser = subparsers.add_parser("convert", help="converts an object from old movai format to pydantic format")
        parser.add_argument("-s", "--db-scope", help="the type of db to use", required=True, default="global")
        parser.add_argument("-d", "--db-id", help="the db id to use", required=True, default=0)
        parser.add_argument("-m", "--models", help="a list of models to convert")
        parser.add_argument("-i", "--ignore", help="a list of models to ignore while converting")

    def parse_model(self, kwargs):
        models_to_convert = kwargs.get("models")
        models_to_ignore = kwargs.get("ignore")

        if models_to_convert is None:
            models_to_convert = set(PYDANTIC_SUPPORTED_MODELS)
        else:
            models_to_convert = set(models_to_convert)
            for model in models_to_convert:
                if model not in PYDANTIC_SUPPORTED_MODELS:
                    self.log.error(f"The requested model: {model} is not supported to be converted into pydantic format.")
                    return 1

        if models_to_ignore is not None:
            for model in models_to_ignore:
                models_to_convert.remove(model)
        
        return models_to_convert

    def execute(self, **kwargs) -> None:
        """Executes the relevant command.
        """
        self.scan_and_convert()

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
            obj = pydantic_class.model_validate(scopes_class(model_name).get_dict())
            obj.save()
            self.log.info(f"Successfully converted the object {model_type}::{model_name} to pydantic")
        except ValidationError:
            self.log.error(f"Got Validation error, while trying to convert object {model_type}::{model_name}")

    def scan_and_convert(self):
        """_summary_

        Args:
            db_type (str): _description_
        """
        invalid_models = set()
        valid_models = set()
        for key in self.keys:
            if "," in key:
                model_type, model_id, *_ = key.split(":")
                model_name = model_id.split(",")[0]
                if model_type not in self.models_to_convert:
                    continue
                if not model_exist(model_type):
                    self.logger.info(f"Could not find {model_type} in new_models, ignoring {model_type}::{model_name}")
                    invalid_models.add(model_type)
                    continue
                valid_models.add(model_type)
                self.convert_model(model_type, model_name)
                self.objects[key] = f"{model_type}:{model_name}"


class Restore(MigrationCommands):
    "Restore operations"

    @classmethod
    def define_arguments(cls, subparsers) -> None:
        """An abstract function for implementing command arguments.

        Args:
            subparsers (_type_): _description_
        """
        parser = subparsers.add_parser("restore", help="restores an object from pydantic format to old movai format")
        parser.add_argument("-m", "--model", help="a model to convert", required=True)
        parser.add_argument("-n", "--name", help="The name of the object to convert")
        parser.add_argument("-i", "--ignore", help="a model to ignore while converting")

    def execute(self, **kwargs) -> None:
        """Executes the relevant command.
        """
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
        #self.register_command(Restore(subparsers))

    def register_command(self, command: BaseCommand):
        """Register the command in dictionary for easy launch by commander.

        Args:
            command (BaseCommand): A command which implement 'execute' function.
            subparsers (_type_): 
        """
        self._commands[command.name] = command

    def run(self, **kwargs):
        command = kwargs.pop("command")
        self._commands[command].safe_execute(**kwargs)


def main():
    tool_description = """The metric tool is a script for manual metric operations.
        it currently supports the following commands: add and get."""
    parser = ArgumentParser(description=tool_description, prog="migrate_tool.py")
    subparsers = parser.add_subparsers(dest="command")
    commander = Commander(subparsers)
    args = parser.parse_args()
    kwargs = convert_list_to_dict(args._get_kwargs())
    commander.run(**kwargs)

if __name__ == "__main__":
    main()
