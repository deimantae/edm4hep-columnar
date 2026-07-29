"""
Helper functions to load and validate user-defined analysis modules
"""

import importlib.util
from pathlib import Path

def load_function(file_name, function_name, section_name):
    if not Path(file_name).is_file():
        raise ValueError(
            f"Invalid '{section_name}' section in the YAML file: "
            f"file '{file_name}' was not found."
        )

    spec = importlib.util.spec_from_file_location(
        f"{section_name}_{function_name}",
        file_name,
    )

    if spec is None or spec.loader is None:
        raise ValueError(
            f"Invalid '{section_name}' section in the YAML file: "
            f"could not load Python file '{file_name}'."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, function_name):
        raise ValueError(
            f"Invalid '{section_name}' section in the YAML file: "
            f"function '{function_name}' was not found in "
            f"'{file_name}'."
        )

    function = getattr(module, function_name)

    if not callable(function):
        raise TypeError(
            f"Invalid '{section_name}' section in the YAML file: "
            f"'{function_name}' in '{file_name}' is not callable."
        )

    return function

def validate_function_config(config, section_name):
    if not isinstance(config, dict):
        raise TypeError(
            f"Invalid '{section_name}' section in the YAML file: "
            "expected a dictionary."
        )

    if "file_name" not in config or "function" not in config:
        raise ValueError(
            f"Invalid '{section_name}' section in the YAML file: "
            "expected both 'file_name' and 'function'."
        )