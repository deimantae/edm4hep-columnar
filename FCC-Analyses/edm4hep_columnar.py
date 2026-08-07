import sys
import yaml
from pathlib import Path
from argparse import ArgumentParser

sys.path.insert(0, str(Path(__file__).parent))

from module_loader import load_function, validate_function_config

# Define the operations on the dataframe
class Analysis:
    
    def __init__(self, cmdline_args):
        # Parse additional arguments
        # All command line arguments are provided in the `cmdline_arg`
        # dictionary and arguments after "--" are stored under "remaining" key.
        parser = ArgumentParser(
            description="Run a configurable EDM4hep analysis.",
            usage="Provided after '--'")
        
        subparsers = parser.add_subparsers(dest="command", required=True)

        # Convert command
        convert_parser = subparsers.add_parser(
            "convert",
            help="Read an EDM4hep file, apply the configured analysis steps "
            "and write the selected variables to an RNTuple"
        )
        convert_parser.add_argument("--parameters-file", required=True,
                                    type=str, help="YAML file containing the analysis configuration.")  

        # EDM4hep histogram command
        edm4hep_parser = subparsers.add_parser(
            "histogram-edm4hep",
            help="Read an EDM4hep file, apply the configured analysis steps "
            "and create histograms."
        )
        edm4hep_parser.add_argument("--parameters-file", required=True, type=str,
                            help="YAML file containing the analysis configuration.")
        
        self.ana_args, _ = parser.parse_known_args(cmdline_args["remaining"])
        self.output_format = 'rntuple'
        
        # Load variables from the YAML configuration file
        config_file = Path(__file__).parent / self.ana_args.parameters_file
        
        # Store YAML contents as a dictionary
        with open(config_file, "r") as file:
            parameters = yaml.safe_load(file)
            
        self.selection = parameters.get("selection")
        self.selection_function = None
        
        if self.selection is not None and "script" in self.selection:
            validate_function_config(
                self.selection["script"],
                "selection.script",
            )
        
            self.selection_function = load_function(
                Path(__file__).parent /
                self.selection["script"]["file_name"],
                self.selection["script"]["function"],
                "selection.script",
            )
                
        self.additional_fields = parameters.get("additional_fields") or []
        self.additional_field_definitions = {}
        
        self.variables = parameters.get("variables") or {}
        
        for field_config in self.additional_fields:
            validate_function_config(
                field_config,
                "additional_fields",
            )
        
            field_function = load_function(
                Path(__file__).parent / field_config["file_name"],
                field_config["function"],
                "additional_fields",
            )
        
            field_definitions = field_function()
            
            if not isinstance(field_definitions, dict):
                raise TypeError(
                    "Additional field function must return a dictionary."
                )
            
            self.additional_field_definitions.update(field_definitions)

        self.branches = []
        
        # Create new branches for every variable defined in the YAML file
        for collection_name, variable_list in self.variables.items():
            if variable_list is None:
                continue # for empty entries
            for variable in variable_list:
                
                # String variable
                if isinstance(variable, str):
                    variable_name = variable
                        
                    if collection_name in self.additional_field_definitions:
                        field_definition = self.additional_field_definitions[
                            collection_name
                        ]
                        
                        expression = field_definition["expression"](
                            collection_name,
                            variable_name,
                        )             
                    else:
                        expression = f"{collection_name}.{variable_name}"
                    
                # Mathematical operation variable
                elif isinstance(variable, dict):
                    if len(variable) != 1:
                        raise ValueError(
                            "Variable definition must contain only"
                            f" one expression: {variable!r}"
                        )
                
                    variable_name, expression = next(iter(variable.items()))
                    
                # If parameters file format is wrong
                else:
                    raise TypeError(
                        f"Unsupported variable definition: {variable!r}"
                    )
                
                branch_name = f"{collection_name}_{variable_name}"
                self.branches.append((branch_name, expression))

    # Return the transformed RDataFrame
    def analyzers(self, dframe):
        
        # Create additional collections
        for field_name, field_definition in (
            self.additional_field_definitions.items()
        ):
            if "define" in field_definition:
                dframe = dframe.Define(
                    field_name,
                    field_definition["define"],
                )
    
        # Apply the event selection
        if self.selection is not None:
            # Use Python selection function
            if self.selection_function is not None:
                dframe = self.selection_function(dframe)
            # Use an inline C++ filter expression
            else:
                dframe = dframe.Filter(self.selection["filter"])
    
        for branch_name, expression in self.branches:
            dframe = dframe.Define(branch_name, expression)
    
        return dframe
    
    # Return the list of branches to save 
    def output(self):
        branches = []
        for branch_name, _ in self.branches:
            branches.append(branch_name)
            
        return branches