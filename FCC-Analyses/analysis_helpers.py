"""
Helper functions for optional analysis steps defined in the YAML configuration.
"""

from module_loader import load_function, validate_function_config


def add_fields(dframe, additional_fields):
    additional_field_definitions = {}

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

        field_definitions = fields_function()

        if not isinstance(field_definitions, dict):
            raise TypeError(
                "Invalid additional-fields function result: "
                f"function '{function_name}' must return a dictionary."
            )

        for field_name, field_definition in field_definitions.items():
            if "define" in field_definition:
                dframe = dframe.Define(
                    field_name,
                    field_definition["define"],
                )

        additional_field_definitions.update(field_definitions)

    return dframe, additional_field_definitions


def apply_selection(dframe, selection):
    if selection is None:
        return dframe

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

        dframe = selection_function(dframe)

    else:
        dframe = dframe.Filter(
            selection["filter"]
        )

    return dframe


def collect_variables(dframe, variables, additional_field_definitions):
    branches = []

    for collection_name, variable_list in variables.items():
        if variable_list is None:
            continue  # for empty entries

        for variable in variable_list:

            if isinstance(variable, str):
                variable_name = variable

                if collection_name in additional_field_definitions:
                    field_definition = additional_field_definitions[
                        collection_name
                    ]

                    expression = field_definition["expression"](
                        collection_name,
                        variable_name,
                    )

                else:
                    expression = f"{collection_name}.{variable_name}"

            elif isinstance(variable, dict):
                if len(variable) != 1:
                    raise ValueError(
                        "Invalid variable definition in the YAML file: "
                        f"expected exactly one expression, got {variable!r}."
                    )

                variable_name, expression = next(iter(variable.items()))

            else:
                raise TypeError(
                    "Invalid variable definition in the YAML file: "
                    f"unsupported variable definition {variable!r}. "
                    "Expected a variable name or a single expression."
                )

            output_name = f"{collection_name}_{variable_name}"

            dframe = dframe.Define(output_name, expression)
            branches.append(output_name)

    return dframe, branches