"""Tool to import, export and remove data."""

import argparse

from dal.utils.usage_search import get_usage_search_scope_map
from dal.tools.usage_search import Searcher
from .backup import backup as backup_main


def main() -> int:
    # Main parser for other actions
    parser = argparse.ArgumentParser(description="Export/Import/Remove/Search Mov.AI Data")
    action_subparser = parser.add_subparsers(dest="action")

    for cmd in ["import", "export", "remove"]:
        sub_parser = action_subparser.add_parser(cmd, help="%s Mov.AI Data" % cmd.capitalize())
        sub_parser.add_argument(
            "action",
            choices=["import", "export", "remove", "usage-search"],
            help="Action to perform: import, export, remove, usage-search",
        )
        sub_parser.add_argument(
            "-m",
            "--manifest",
            help="Manifest with declared objects to export/import/remove. ex.: Flow:Myflow",
            type=str,
            required=False,
            metavar="",
        )
        sub_parser.add_argument(
            "-p",
            "--project",
            help="Folder to export to or import from (not required for usage-search).",
            type=str,
            required=True,
            metavar="",
        )
        sub_parser.add_argument(
            "-t",
            "--type",
            help="Object type. Options: Flow, Node, StateMachine, Callback, Annotation.",
            type=str,
            metavar="",
            default=None,
        )
        sub_parser.add_argument(
            "-n",
            "--name",
            help="Object name (required for usage-search operations)",
            type=str,
            metavar="",
            default=None,
        )
        sub_parser.add_argument(
            "-f",
            "--force",
            dest="force",
            action="store_true",
            help="Do not validate newly inserted instances",
        )
        sub_parser.add_argument(
            "-v",
            "--verbose",
            dest="debug",
            action="store_true",
            help="Print progress information",
        )
        sub_parser.add_argument(
            "-d",
            "--dry",
            "--dry-run",
            dest="dry",
            action="store_true",
            help="Don't actually import or remove anything, simply print the file paths",
        )
        sub_parser.add_argument(
            "-i",
            "--individual",
            dest="individual",
            action="store_true",
            help="Only export/import/remove the element, not the dependencies",
        )
        sub_parser.add_argument(
            "-c",
            "--clean",
            dest="clean_old_data",
            action="store_true",
            help="Clean old data, after import",
        )

        sub_parser.set_defaults(force=False, debug=False, dry=False)

    # arguments for usage-search
    sub_parser = action_subparser.add_parser(
        "usage-search", help="Search for usage of a Node or Flow"
    )
    sub_parser.add_argument(
        "search_type",
        choices=list(get_usage_search_scope_map().keys()),
        help="Scope to search for",
    )
    sub_parser.add_argument("name", help="Name of the node to search for")
    sub_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    args = parser.parse_args()

    if args.action == "usage-search":
        searcher = Searcher(debug=args.verbose)
        ret_code = searcher.search_usage(args.search_type, args.name)
    elif args.action in ["import", "export", "remove"]:
        # Non usage-search actions require project
        if not args.project:
            parser.error(f"{args.action} requires --project argument")
        ret_code = backup_main(args)
    else:
        parser.print_help()
        ret_code = 0

    return ret_code


if __name__ == "__main__":
    exit(main())
