import yaml
from pathlib import Path

#Define the operations on the dataframe
class Analysis:
    
    def __init__(self, cmdline_args):
        self.process_list = {}
        self.input_dir = '/eos/experiment/fcc/hh/tutorials/'\
            'edm4hep_tutorial_data/'
        self.output_dir = "outputs/opens-fccanalyses"
        self.test_file = 'https://fccsw.web.cern.ch/fccsw/analysis/' \
                         'test-samples/edm4hep099/p8_ee_WW_ecm240_edm4hep.root'
        
        #Load variables from the YAML configuration file
        config_file = Path(__file__).parent / "jet_variables.yaml"
        
        #Store YAML contents as a dictionary
        with open(config_file, "r") as file:
            self.variables = yaml.safe_load(file)

    #Return the transformed RDataFrame
    def analyzers(self, dframe):
        #Create new branches for every variable defined in the YAML file
        for branch_name, branch_info in self.variables.items():
            dframe = dframe.Define(
                branch_name,
                branch_info["line"]
                )
        
        return dframe
    
    #Return the list of branches to save
    def output(self):
        return list(self.variables.keys())
    
    #rntuple?
    #mass charge Jet.goodnessOfPID #now use these, we will have one that is computing and some in the file
    
    
