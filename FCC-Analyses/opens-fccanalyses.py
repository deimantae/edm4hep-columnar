import yaml
import importlib.util
from pathlib import Path
from argparse import ArgumentParser

# Define the operations on the dataframe
class Analysis:
    
    def __init__(self, cmdline_args):
        # Parse additional arguments
        # All command line arguments are provided in the `cmdline_arg`
        # dictionary and arguments after "--" are stored under "remaining" key.
        parser = ArgumentParser(
            description="Additional analysis arguments",
            usage="Provided after '--'")
        parser.add_argument("--parameters-file", required=True, type=str,
                            help="YAML file containing the variables.")
        self.ana_args, _ = parser.parse_known_args(cmdline_args["remaining"])

        # Run over the full statistics and save it to one output file named
        # <outputDir>/<process_name>.root
        self.process_list = {
                'p8_ee_ZZ_ecm240': {'fraction': 0.5}, #  statistics percent
                'p8_ee_WW_ecm240': {'fraction': 0.25},
                'p8_ee_ZH_ecm240': {'fraction': 0.2,}
        }
        self.output_format = 'rntuple'
        self.input_dir = "/eos/experiment/fcc/hh/tutorials/"\
            "edm4hep_tutorial_data/"
        self.output_dir = "outputs/opens-fccanalyses"
        self.test_file = "https://fccsw.web.cern.ch/fccsw/analysis/" \
                         "test-samples/edm4hep099/p8_ee_WW_ecm240_edm4hep.root"
        
        # Load variables from the YAML configuration file
        config_file = Path(__file__).parent / self.ana_args.parameters_file
        
        # Store YAML contents as a dictionary
        with open(config_file, "r") as file:
            parameters = yaml.safe_load(file)
            
        self.selection = parameters.get("selection")
        self.variables = parameters.get("variables", {})
        self.selection_function = None
        
        if self.selection is not None:
            has_file = "file" in self.selection
            has_function = "function" in self.selection
            has_filter = "filter" in self.selection

            # File and function must always be specified together
            if has_file != has_function:
                raise ValueError(
                    "'file' and 'function' must be specified together."
                )

            # Only one selection method may be used
            if has_file and has_filter:
                raise ValueError(
                    "Selection must use either 'file' + 'function' "
                    "or 'filter', not both."
                )

            if not has_file and not has_filter:
                raise ValueError(
                    "Selection must contain either 'file' + 'function' "
                    "or 'filter'."
                )

            if has_file:
                selection_file = (
                    Path(__file__).parent / self.selection["file"]
                )
        
                spec = importlib.util.spec_from_file_location(
                    "event_selection",
                    selection_file,
                )

                selection_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(selection_module)

                self.selection_function = getattr(
                    selection_module,
                    self.selection["function"],
                )
        
        self.branches = []
        
        # Create new branches for every variable defined in the YAML file
        for collection_name, variable_list in self.variables.items():
            if variable_list is None:
                continue # for empty entries
            for variable in variable_list:
                
                # String variable
                if isinstance(variable, str):
                    variable_name = variable

                    if collection_name in {"Muon", "Electron", "Photon"}:
                        expression = (
                            f"FCCAnalyses::ReconstructedParticle::"
                            f"get_{variable_name}({collection_name})"
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
                
                    for variable_name, expression in variable.items():
                        pass
                    
                # If parameters file format is wrong
                else:
                    raise TypeError(
                        f"Unsupported variable definition: {variable!r}"
                    )
                
                branch_name = f"{collection_name}_{variable_name}"
                self.branches.append((branch_name, expression))

    # Return the transformed RDataFrame
    def analyzers(self, dframe):
        
        # Create Muon, Electron and Photon collections from ReconstructedParticles
        if self.variables.get("Muon") is not None:
            dframe = dframe.Define(
                "Muon",
                "FCCAnalyses::ReconstructedParticle::get("
                "Muon_objIdx.index, ReconstructedParticles)"
            )
    
        if self.variables.get("Electron") is not None:
            dframe = dframe.Define(
                "Electron",
                "FCCAnalyses::ReconstructedParticle::get("
                "Electron_objIdx.index, ReconstructedParticles)"
            )
    
        if self.variables.get("Photon") is not None:
            dframe = dframe.Define(
                "Photon",
                "FCCAnalyses::ReconstructedParticle::get("
                "Photon_objIdx.index, ReconstructedParticles)"
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