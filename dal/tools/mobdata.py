"""Tool to import, export and remove data."""

import argparse

from .backup import backup as backup_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Export/Import/Remove/Search Mov.AI Data")
    parser.add_argument(
        "action",
        choices=["import", "export", "remove", "search"],
        help="Action to perform: import, export, remove, search (use with --type), search-node (use with --name), or search-flow (use with --name)",
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
        help="Folder to export to or import from (not required for search).",
        type=str,
        required=False,
        metavar="",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Object type. Options: Flow, Node, StateMachine, Callback, Annotation. For 'search' action, specify 'Node' or 'Flow'.",
        type=str,
        metavar="",
        default=None,
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Object name (required for search operations)",
        type=str,
        metavar="",
        default=None,
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="Search for usages recursively.",
        dest="recursive",
        action="store_true",
    )
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

    # Validate arguments based on action
    if args.action == "search":
        # Search doesn't require project but requires name
        if not args.type:
            parser.error("search action requires --type argument ('Node' or 'Flow')")
        if not args.name:
            parser.error(f"{args.action} requires --name argument")
    else:
        # Other actions require project
        if not args.project:
            parser.error(f"{args.action} requires --project argument")

    ret_code = backup_main(args)

    return ret_code


if __name__ == "__main__":
    exit(main())
