"""
Helper functions for optional analysis steps defined in the YAML configuration.
"""
import ROOT

from module_loader import load_function, validate_function_config

# Add collections defined in the YAML
def add_fields(dframe, additional_fields):
    for field_name, expression in additional_fields.items():
        dframe = dframe.Define(field_name, expression)

    return dframe


def resolve_function(collection_name, function_name):
    # Check FCCAnalyses helpers first
    podio_namespace = ROOT.FCCAnalyses.PodioSource.ReconstructedParticle

    if hasattr(podio_namespace, function_name):
        return (
            "FCCAnalyses::PodioSource::ReconstructedParticle::"
            f"{function_name}({collection_name})"
        )

    # Check user-defined helpers
    custom_namespace = ROOT.EDM4hepColumnar

    if hasattr(custom_namespace, function_name):
        return (
            "EDM4hepColumnar::"
            f"{function_name}({collection_name})"
        )

    raise ValueError(
        f"Function '{function_name}' was not found for "
        f"collection '{collection_name}'."
    )


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


def collect_variables(dframe, variables):
    branches = []

    for collection_name, variable_list in variables.items():
        if variable_list is None:
            continue

        for variable in variable_list:
            if not isinstance(variable, dict) or len(variable) != 1:
                raise ValueError(
                    "Invalid variable definition in the YAML file: "
                    f"expected 'name: function/expression', got {variable!r}."
                )

            variable_name, value = next(iter(variable.items()))

            if not isinstance(value, str):
                raise TypeError(
                    "Invalid variable definition in the YAML file: "
                    f"expected a string, got {value!r}."
                )

            # Simple function name, e.g. pt: getPt
            if value.isidentifier():
                expression = resolve_function(collection_name, value)

            # Full C++ expression
            else:
                expression = value

            output_name = f"{collection_name}_{variable_name}"

            dframe = dframe.Define(output_name, expression)
            branches.append(output_name)

    return dframe, branches
