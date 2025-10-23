import argparse
import sys
from pathlib import Path

import enronmail.utils as utils
import enronmail.database as database
import enronmail.analysis as analysis


def main():
    parser = argparse.ArgumentParser(description="Enron Email Corpus Analysis Tool")

    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Initialize database command
    init_db_parser = subparsers.add_parser(
        "init-db", help="Initialize the SQL database"
    )
    init_db_parser.add_argument(
        "--maildir",
        type=str,
        default="maildir",
        help="Path to the maildir directory containing the emails",
    )
    init_db_parser.add_argument(
        "--pickle-path",
        type=str,
        default="pickle/file_list.pickle",
        help="Path to the pickle file containing the file list",
    )
    init_db_parser.add_argument(
        "--generate-file-list",
        action="store_true",
        help="Generate file list before populating database",
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "init-db":
        # Initialize the database table
        database.init_table()

        # Generate file list if requested
        if args.generate_file_list:
            file_list = analysis.generate_file_list(
                Path(args.maildir), args.pickle_path
            )
        else:
            # Load existing file list
            file_list = utils.load_pickle(args.pickle_path)

        # Populate database with email data
        database.populate_database(file_list)
        print("Database initialization complete")
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
