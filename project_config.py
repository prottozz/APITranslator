# project_config.py
from pathlib import Path
import sys

# Assuming Project.py is in the same directory or Python path
# Add the directory of Project.py to sys.path if it's not already
# For example, if Project.py is in a 'backend' subdirectory:
# script_dir = Path(__file__).resolve().parent
# backend_dir = script_dir / 'backend'
# sys.path.append(str(backend_dir))

try:
    from Project import Config, logger as backend_logger # Import your existing Config and logger
    CONFIG_FILE_PATH = Path('./config.yml') # Or 'config_sample.yml'
    if not CONFIG_FILE_PATH.exists():
        # Attempt to create a default one if Project.py handles this, or provide a default
        print(f"Warning: {CONFIG_FILE_PATH} not found. Using default paths or expecting Project.py to handle.")
        # Potentially copy config_sample.yml to config.yml here if desired
        # import shutil
        # if Path('./config_sample.yml').exists():
        #     shutil.copy('./config_sample.yml', CONFIG_FILE_PATH)
        # else:
        #     raise FileNotFoundError("config.yml or config_sample.yml not found.")

    config_instance = Config(CONFIG_FILE_PATH)
except ImportError as e:
    print(f"Error importing from Project.py: {e}. Ensure Project.py is accessible.")
    print("Please place Project.py in the same directory or adjust the sys.path.")
    # Fallback if Project.py cannot be imported, so the UI can at least start
    class DummyConfig:
        def get(self, *keys, default=None): return default
        def set(self, value, *keys): pass
        def save(self): pass
    config_instance = DummyConfig()
    backend_logger = None # No backend logger if Project.py fails
except FileNotFoundError as e:
    print(f"Configuration file error: {e}")
    class DummyConfig:
        def get(self, *keys, default=None): return default
        def set(self, value, *keys): pass
        def save(self): pass
    config_instance = DummyConfig()
    backend_logger = None


def get_config():
    """Returns the global config instance."""
    # Optionally, implement logic to reload config if needed
    return config_instance

def get_backend_logger():
    return backend_logger