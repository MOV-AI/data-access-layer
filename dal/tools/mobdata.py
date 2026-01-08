"""Tool to import, export and remove data."""

import argparse
import sys

from dal.tools.usage_search import Searcher
from .backup import backup as backup_main


def main() -> int:
    # Special handling for usage-search to allow subparser help to work properly
    if len(sys.argv) > 1 and sys.argv[1] == "usage-search":
        search_parser = argparse.ArgumentParser(
            prog="mobdata usage-search",
            description="Search for usage of a Node or Flow",
        )
        search_subparsers = search_parser.add_subparsers(
            dest="search_type",
            help="Type of object to search for",
        )

        # Node search
        node_parser = search_subparsers.add_parser(
            "node",
            help="Search for node usage",
        )
        node_parser.add_argument("name", help="Name of the node to search for")
        node_parser.add_argument(
            "-i",
            "--individual",
            action="store_true",
            help="Include only direct usage (exclude indirect usage through subflows)",
        )
        node_parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Print detailed progress information",
        )

        # Flow search
        flow_parser = search_subparsers.add_parser(
            "flow",
            help="Search for flow usage as a subflow",
        )
        flow_parser.add_argument("name", help="Name of the flow to search for")
        flow_parser.add_argument(
            "-i",
            "--individual",
            action="store_true",
            help="Include only direct usage (exclude indirect usage through nested subflows)",
        )
        flow_parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Print detailed progress information",
        )

        # Parse just the usage-search arguments (skip 'usage-search' itself)
        search_args = search_parser.parse_args(sys.argv[2:])

        if not search_args.search_type:
            search_parser.print_help()
            return 1

        searcher = Searcher(debug=search_args.verbose)

        if search_args.search_type == "node":
            result = searcher.search_node_usage(
                search_args.name, recursive=not search_args.individual
            )
            searcher.print_results(result, "node")
        elif search_args.search_type == "flow":
            result = searcher.search_flow_usage(
                search_args.name, recursive=not search_args.individual
            )
            searcher.print_results(result, "flow")

        if "error" in result and "does not exist" not in result["error"]:
            return 1
        return 0

    # Main parser for other actions
    parser = argparse.ArgumentParser(description="Export/Import/Remove/Search Mov.AI Data")
    parser.add_argument(
        "action",
        choices=["import", "export", "remove", "usage-search"],
        help="Action to perform: import, export, remove, usage-search",
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
        help="Folder to export to or import from (not required for usage-search).",
        type=str,
        required=False,
        metavar="",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Object type. Options: Flow, Node, StateMachine, Callback, Annotation.",
        type=str,
        metavar="",
        default=None,
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Object name (required for usage-search operations)",
        type=str,
        metavar="",
        default=None,
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

    args = parser.parse_args()

    # Non usage-search actions require project
    if not args.project:
        parser.error(f"{args.action} requires --project argument")

    ret_code = backup_main(args)

    return ret_code


if __name__ == "__main__":
    exit(main())
