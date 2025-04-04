from abc import ABC, abstractmethod
import argparse
from ctypes import ArgumentError
from curses.ascii import isascii
from errno import EEXIST, EINVAL, ENOEXEC

from movai_core_shared.logger import Log
from movai_core_shared.exceptions import SecretKeyAlreadyExist, SecretKeyDoesNotExist

from dal.classes.utils.secretkey import SecretKey

MIN_KEY_LENGTH = 16
MAX_KEY_LENGTH = 1024


class BaseCommand(ABC):
    """Base Class for the varios tool commands."""

    log = Log.get_logger("BaseCommand")

    def __init__(self, **kwargs) -> None:
        """initializes the object and extract commnad arguments."""
        self.command = kwargs["command"]
        self.name = kwargs.get("name")
        self.length = kwargs.get("length", 32)
        self.log.debug(f"executing {self.command} command.")

    def __call__(self) -> any:
        """Executes the relevant command

        Returns:
            any: returns the command output.
        """
        try:
            return self.execute()
        except SecretKeyDoesNotExist as e:
            print(e)
            return ENOEXEC
        except SecretKeyAlreadyExist as e:
            print(e)
            return EEXIST
        except ArgumentError as e:
            print(e)
            return EINVAL

    def fail_argument(self, arg_name: str):
        """A general function for raising ArgumentError.

        Args:
            arg_name (str): The name of the argument to check

        Raises:
            ArgumentError: In case the argument is missing.
        """
        error_msg = f"Can't execute {self.command} command, the {arg_name} argument is missing."
        raise ArgumentError(error_msg)

    def check_name(self):
        """Checks the name argument"""
        error = False
        if self.name is None:
            self.fail_argument("name")
        if not isinstance(self.name, str):
            self.fail_argument("name")
        for letter in self.name:
            if not isascii(letter):
                self.fail_argument("name")

    def check_length(self):
        """Checks the legnth argument

        Raises:
            ArgumentError: in case the length argument is missing or his value
                is not in the allowed range.
        """
        if self.length is None:
            self.fail_argument("length")
        elif self.length < 16 or self.length > 1024:
            error_msg = (
                f"Can't execute {self.command} command,"
                f"the length argument must be in the range {MIN_KEY_LENGTH} to {MAX_KEY_LENGTH}."
            )
            raise ArgumentError(error_msg)

    @abstractmethod
    def execute(self) -> int:
        """Abstract funtion for exuting command.

        Returns:
            any: output from the command.
        """


class CreateCommand(BaseCommand):
    """Creates an new secret key in DB.

    Args:
        name (str) - the name of the key object in DB.
        length (int) - the size of the key in characters.
    """

    def execute(self) -> int:
        self.check_name()
        self.check_length()
        SecretKey.create(self.name, self.length)
        print(f"successfully created {self.name} secret key.")
        return 0


class RemoveCommand(BaseCommand):
    """Removes a key from DB.

    Args:
        name (str) - the name of the key object in DB.
    """

    def execute(self) -> int:
        self.check_name()
        SecretKey.remove(self.name)
        print(f"successfully removed {self.name} secret key.")
        return 0


class UpdateCommand(BaseCommand):
    """Updates a key in DB.

    Args:
        name (str) - the name of the key object in DB.
        length (int) - the size of the key in characters.
    """

    def execute(self) -> int:
        self.check_name()
        self.check_length()
        SecretKey.update(self.name, self.length)
        print(f"successfully updated {self.name} secret key.")
        return 0


class ShowCommand(BaseCommand):
    """Dispalys the the key on the user terminal."""

    def execute(self) -> int:
        self.check_name()
        print(f"Secret: {SecretKey.get_secret(self.name)}")
        return 0


class SecretKeyTool:
    """A class for executing the correct command"""

    commands = {
        "create": CreateCommand,
        "remove": RemoveCommand,
        "update": UpdateCommand,
        "show": ShowCommand,
    }

    def __call__(self, **kwargs):
        """initialize the tool and execute the command."""
        if "command" not in kwargs:
            error_msg = f"Can not find the command field in kwargs dictionary."
            print(error_msg)
            return EINVAL
        command = kwargs["command"]
        if command not in self.commands:
            error_msg = f"Unknown command: {command}"
            print(error_msg)
            return EINVAL
        command_type = self.commands[command]
        command_obj = command_type(**kwargs)
        return command_obj()


def main():
    parser = argparse.ArgumentParser(description="Create a secret key for Mov.ai fleet.")
    parser.add_argument(
        "-c",
        "--command",
        help="create - creates a new key with the specified name"
        "remove - removes the key with the specified name"
        "update - updates the key with the specified name"
        "show - displays thecontents of key with the specified name"
        "list - list all available keys on current robot",
        type=str,
        required=True,
    )
    parser.add_argument("-n", "--name", help="key name", type=str, required=False)
    parser.add_argument(
        "-l",
        "--length",
        help=f"key length, default = 64, {MIN_KEY_LENGTH} =< length =< {MAX_KEY_LENGTH}",
        type=int,
        required=False,
    )

    args, _ = parser.parse_known_args()

    key = SecretKeyTool()
    exit(key(**vars(args)))


if __name__ == "__main__":
    main()
