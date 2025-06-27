"""Tool to import, export and remove data."""

import argparse

from .backup import main as backup_main


def main():
    parser = argparse.ArgumentParser(description="Export/Import/Remove Mov.AI Data")
    parser.add_argument(
        "action", choices=["import", "export", "remove"], help="Import, export or remove"
    )
    parser.add_argument(
        "-m",
        "--manifest",
        help="Manifest with declared objects to export/import/remove. ex.: Flow:Myflow",
        type=str,
        required=False,
        metavar="",
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Folder to export to or import from.",
        type=str,
        required=True,
        metavar="",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Object type. Options: Flow, StateMachine, Node, Callback, Annotation",
        type=str,
        metavar="",
        default=None,
    )
    parser.add_argument("-n", "--name", help="Object name", type=str, metavar="", default=None)
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Do not validate newly inserted instances",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="debug",
        action="store_true",
        help="Print progress information",
    )
    parser.add_argument(
        "-d",
        "--dry",
        "--dry-run",
        dest="dry",
        action="store_true",
        help="Don't actually import or remove anything, simply print the file paths",
    )
    parser.add_argument(
        "-i",
        "--individual",
        dest="individual",
        action="store_true",
        help="Only export/import/remove the element, not the dependencies",
    )
    parser.add_argument(
        "-c",
        "--clean",
        dest="clean_old_data",
        action="store_true",
        help="Clean old data, after import",
    )

    parser.set_defaults(force=False, debug=False, dry=False)

    args, _ = parser.parse_known_args()

    ret_code = backup_main(args)

    exit(ret_code)


if __name__ == "__main__":
    main()
