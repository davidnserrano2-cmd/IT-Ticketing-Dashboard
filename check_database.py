r"""Run locally: .\.venv\Scripts\python.exe check_database.py"""

import json
import sys

import psycopg

from database import database_summary


if __name__ == "__main__":
    try:
        result = database_summary()
    except ValueError as error:
        print(error)
        sys.exit(1)
    except psycopg.Error as error:
        # Do not print connection arguments or arbitrary exception details.
        if isinstance(error, psycopg.errors.InvalidPassword):
            print("Password was rejected. Check the reader account's local password.")
        elif isinstance(error, psycopg.errors.InsufficientPrivilege):
            print("Reader account is missing a required SELECT or connection permission.")
        else:
            print("Database check failed. Check host, port, database, role, and password locally.")
        sys.exit(1)
    print(json.dumps(result, indent=2))
