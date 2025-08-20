from ast import Attribute, Constant, JoinedStr, Name, NodeVisitor, Call, PyCF_ONLY_AST
import astunparse
from dataclasses import dataclass
from typing import List
import logging
import sys
import os
from datetime import datetime

from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po
from babel.core import Locale, UnknownLocaleError


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
                    log_string = astunparse.unparse(first_arg).strip()
                    is_f_string = False
                    if isinstance(first_arg, JoinedStr):
                        # We don't want the leading 'f' from f-strings, they're just strings to us
                        log_string = log_string[2:-1]
                        is_f_string = True
                    elif isinstance(first_arg, Constant) and isinstance(first_arg.value, str):
                        log_string = first_arg.value[1:-1]
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
                    logging.warning("Failed to read or parse file {file_path}", exc_info=True)
    return all_strings


def make_po_file(strings: List[SourceString], output_path: str, locale: Locale) -> None:
    """
    Write extracted strings to a .po file for translation using Babel.

    Args:
        strings (List[SourceString]): List of SourceString objects to write.
        output_path (str): Path to save the .po file.
        locale (str): Locale code for the .po file.
    """
    catalog = Catalog(
        creation_date=datetime.now(),
        locale=locale,
    )
    for string in strings:
        comments = ["[F-string]"] if string.is_f_string else []
        catalog.add(
            string.value, locations=[(string.filename, string.lineno)], auto_comments=comments
        )

    with open(output_path, "wb") as po_file:
        write_po(po_file, catalog)


def locale_type(value):
    try:
        return Locale.parse(value)
    except UnknownLocaleError:
        raise argparse.ArgumentTypeError(f"Locale '{value}' is not recognized by Babel.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract i18n strings from Python files and generate a .po file."
    )
    parser.add_argument("dir_path", help="Directory containing Python files to scan")
    parser.add_argument("output_path", help="Path to save the .po file")
    parser.add_argument(
        "locale", type=locale_type, help="Locale code for the .po file (e.g. en, fr, pt_BR)"
    )

    args = parser.parse_args()

    # Check if output file exists and confirm overwrite
    if os.path.exists(args.output_path):
        response = (
            input(f"File '{args.output_path}' already exists. Overwrite? [y/N]: ").strip().lower()
        )
        if response != "y":
            print("Aborted.")
            exit(1)

    strings = parse_directory(args.dir_path)
    print(
        f"Extracted {len(strings)} strings from {args.dir_path}\nWriting to {args.output_path}",
        file=sys.stderr,
    )
    make_po_file(strings, args.output_path, args.locale)
