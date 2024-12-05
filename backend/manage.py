#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")  # Set the default settings module to your backend.settings
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # This will raise an ImportError if Django is not installed.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable?"
            )
        raise
    execute_from_command_line(sys.argv)
