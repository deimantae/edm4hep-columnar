"""
Helper functions for optional analysis steps defined in the YAML configuration.
"""

import awkward as ak
import numpy as np

from module_loader import load_function, validate_function_config

def add_fields(events, additional_fields):
    for field_config in additional_fields:
        validate_function_config(
            field_config,
            "additional_fields",
        )

        function_name = field_config["function"]

        fields_function = load_function(
            field_config["file_name"],
            function_name,
            "additional_fields",
        )

        new_fields = fields_function(events)

        if not isinstance(new_fields, dict):
            raise TypeError(
                "Invalid additional-fields function result: "
                f"function '{function_name}' must return a dictionary."
            )

        for field_name, field_values in new_fields.items():
            events = ak.with_field(
                events,
                field_values,
                field_name,
            )

    return events

def apply_selection(events, selection):
    if selection is None:
        return events

    if not isinstance(selection, dict):
        raise TypeError(
            "Invalid 'selection' section in the YAML file: "
            "expected a dictionary."
        )

    has_script = "script" in selection
    has_filter = "filter" in selection

    if has_script and has_filter:
        raise ValueError(
            "Invalid 'selection' section in the YAML file: "
            "use either 'script' or 'filter', not both."
        )

    if not has_script and not has_filter:
        raise ValueError(
            "Invalid 'selection' section in the YAML file: "
            "expected either 'script' or 'filter'."
        )

    if has_script:
        script_config = selection["script"]

        validate_function_config(
            script_config,
            "selection.script",
        )

        selection_function = load_function(
            script_config["file_name"],
            script_config["function"],
            "selection.script",
        )

        mask = selection_function(events)

    else:
        filter_namespace = {
            "ak": ak,
            "np": np,
        }

        for collection_name in events.fields:
            filter_namespace[collection_name] = getattr(
                events,
                collection_name,
            )

        mask = eval(
            selection["filter"],
            filter_namespace,
        )

    print("Selected events:", ak.sum(mask))
    print("Rejected events:", ak.sum(~mask))

    return events[mask]

def collect_variables(events, variables):
    variables_output = {}

    for collection_name, variable_list in variables.items():
        if variable_list is None:
            continue  # for empty entries

        collection = getattr(events, collection_name)

        for variable in variable_list:

            if isinstance(variable, str):
                variable_name = variable
                values = getattr(collection, variable_name)

            elif isinstance(variable, dict):
                if len(variable) != 1:
                    raise ValueError(
                        "Invalid variable definition in the YAML file: "
                        f"expected exactly one expression, got {variable!r}."
                    )

                for variable_name, expression in variable.items():
                    for field in collection.fields:
                        expression = expression.replace(
                            field,
                            f"collection.{field}",
                        )

                    values = eval(expression)

            else:
                raise TypeError(
                    "Invalid variable definition in the YAML file: "
                    f"unsupported variable definition {variable!r}. "
                    "Expected a variable name or a single expression."
                )

            output_name = f"{collection_name}_{variable_name}"
            variables_output[output_name] = values

    return variables_output
