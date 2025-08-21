import json
import logging
import os
import sys
from ast import Attribute, Call, Constant, JoinedStr, Name, NodeVisitor, PyCF_ONLY_AST
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from typing import List

from babel.core import Locale
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

try:
    from ast import unparse
except ImportError:
    # astunparse is a backport for Python < 3.9
    from astunparse import unparse


@dataclass
class SourceString:
    """
    Represents a string extracted from source code, along with its location.

    Attributes:
        value (str): The extracted string value.
        lineno (int): The line number in the source file where the string appears.
        col_offset (int): The column offset in the source file.
        filename (str): The name of the source file.
    """

    value: str
    lineno: int
    col_offset: int
    filename: str
    is_f_string: bool


class CallVisitor(NodeVisitor):
    """
    AST visitor that collects strings from logging function calls
    where the 'ui' keyword argument is set to True.

    Attributes:
        filename (str): The name of the file being parsed.
        strings (List[SourceString]): List of extracted SourceString objects.
    """

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.strings: List[SourceString] = []

    def visit_Call(self, funccall: "Call") -> None:
        """
        Visits each function call node in the AST. If the call is to a logging function
        ('info', 'warning', 'error', or 'exception') and has a keyword argument 'ui=True',
        it extracts the first argument (the log message) as a string. The extracted string,
        along with its location (line number, column offset, and filename), is stored for
        later use. Handles both regular strings and f-strings, and falls back to a placeholder
        if the argument type is unexpected.
        """
        if isinstance(funccall.func, Name):
            # plain function calls, like "info()"
            call_name = funccall.func.id
        elif isinstance(funccall.func, Attribute):
            # this is for method calls, like "logger.info()"
            call_name = funccall.func.attr
        else:
            self.generic_visit(funccall)
            return

        if call_name in ("info", "warning", "error", "exception"):
            for keyword in funccall.keywords:
                if (
                    keyword.arg == "ui"
                    and isinstance(keyword.value, Constant)
                    and keyword.value.value is True
                ):
                    first_arg = funccall.args[0]
                    log_string = unparse(first_arg).strip()
                    is_f_string = False
                    if isinstance(first_arg, JoinedStr):
                        # We don't want the leading 'f' from f-strings, they're just strings to us
                        log_string = log_string[2:-1]
                        is_f_string = True
                    elif isinstance(first_arg, Constant) and isinstance(first_arg.value, str):
                        log_string = log_string[1:-1]
                    else:
                        log_string = f"<{log_string}>"

                    self.strings.append(
                        SourceString(
                            value=log_string,
                            lineno=first_arg.lineno,
                            col_offset=first_arg.col_offset,
                            filename=self.filename,
                            is_f_string=is_f_string,
                        )
                    )

        self.generic_visit(funccall)


def parse_code(code: str, filename: str) -> List[SourceString]:
    """
    Parse Python source code and extract strings from logging calls
    with 'ui=True'.

    Args:
        code (str): The Python source code to parse.
        filename (str): The name of the source file.

    Returns:
        List[SourceString]: List of extracted SourceString objects.
    """
    try:
        tree = compile(code, "<string>", "exec", PyCF_ONLY_AST)
        visitor = CallVisitor(filename)
        visitor.visit(tree)
        return visitor.strings
    except Exception:
        logging.warning("Failed to parse code", exc_info=True)
        return []


def parse_directory(dir_path: str) -> List[SourceString]:
    """
    Recursively parse all Python files in a directory, extracting
    strings from logging calls with 'ui=True'.

    Args:
        dir_path (str): Path to the directory containing Python files.

    Returns:
        List[SourceString]: List of all extracted SourceString objects.
    """
    all_strings = []

    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        code = file.read()
                        strings = parse_code(code, file_path)
                        for string in strings:
                            string.filename = file_path
                            all_strings.append(string)
                except Exception as e:
                    logging.warning(
                        "Failed to read or parse file %s: %s", file_path, e, exc_info=True
                    )
    return all_strings


def make_po_file(strings: List[SourceString], output_path: str, name: str, locale: Locale) -> None:
    """
    Write extracted strings to a .po file for translation using Babel.

    Args:
        strings (List[SourceString]): List of SourceString objects to write.
        output_path (str): Directory to save the .po file.
        name (str): Name of the metadata translation file.
        locale (str): Locale code for the .po file.
    """
    po_path = os.path.join(output_path, f"{name}_{locale.language}.po")
    catalog = Catalog(
        creation_date=datetime.now(),
        locale=locale,
    )
    for string in strings:
        comments = ["[F-string]"] if string.is_f_string else []
        catalog.add(
            string.value, locations=[(string.filename, string.lineno)], auto_comments=comments
        )

    with open(po_path, "wb") as po_file:
        write_po(po_file, catalog)


def make_json_file(output_path: str, name: str) -> None:
    """
    Create a JSON file that lists the metadata translation file.

    Args:
        output_path (str): Directory to save the JSON file.
        name (str): Name of the metadata translation file.
    """
    json_path = os.path.join(output_path, f"{name}.json")

    with open(json_path, "w", encoding="utf-8") as json_file:
        json_file.write(
            json.dumps(
                {
                    "Translation": {
                        name: {
                            "Label": name,
                            "LastUpdate": {
                                "date": datetime.now().strftime("%d/%m/%Y at %H:%M:%S"),
                                "user": "movai@internal",
                            },
                        }
                    }
                },
                indent=4,
            )
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Extract i18n strings from Python files and generate a .po file.\n"
            "The tool will:\n\n"
            "* Look for ui=True logs\n"
            "* Perform reasonable changes to the .py files\n"
            "* Collect logs\n"
            "* Write logs in the translation file\n"
            "* Append the translation file to the manifest.txt\n"
        ),
    )
    parser.add_argument(
        "-d",
        "--dir",
        nargs=1,
        action="append",
        required=True,
        help="Directories containing Python files to scan (can be used multiple times)",
    )
    parser.add_argument("-n", "--name", required=True, help="Name of the metadata translation file")
    parser.add_argument(
        "-p",
        "--output-path",
        required=True,
        help="Metadata folder where to save the translation file",
    )

    args = parser.parse_args()

    print(f"Extracting i18n strings from directories: {args.dir}")

    # Check if output file exists and confirm overwrite
    if os.path.exists(args.output_path):
        response = (
            input(f"Directory '{args.output_path}' already exists. Overwrite? [y/N]: ")
            .strip()
            .lower()
        )
        if response != "y":
            print("Aborted.")
            exit(1)

    strings = list(chain.from_iterable(parse_directory(dir[0]) for dir in args.dir))
    print(
        f"Extracted {len(strings)} strings.\nWriting to {args.output_path}",
        file=sys.stderr,
    )

    try:
        os.mkdir(args.output_path)
    except FileExistsError:
        pass
    make_po_file(strings, args.output_path, args.name, Locale.parse("pt"))
    make_json_file(args.output_path, args.name)


if __name__ == "__main__":
    main()
