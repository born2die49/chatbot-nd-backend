#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    # Determine the directory containing manage.py
    manage_py_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to .env.dev, assuming it's in the same directory as manage.py
    dotenv_path = os.path.join(manage_py_dir, '.env.dev') # <--- ADD THIS

    if os.path.exists(dotenv_path): # <--- ADD THIS
        load_dotenv(dotenv_path=dotenv_path) # <--- ADD THIS
    else: # <--- ADD THIS (Optional: for debugging)
        print(f"Warning: .env.dev file not found at {dotenv_path}") # <--- ADD THIS
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'd_chatbot.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
