import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from edm4hep_columnar import Analysis as _Analysis


# Parse command-line arguments
parser = ArgumentParser(add_help=False)

parser.add_argument("--input-file", required=True)

parser.add_argument("--output-file", required=True)

# Arguments for analysis given after "--"
if "--" not in sys.argv:
    raise RuntimeError(
        'Expected analysis arguments after "--".'
    )

analysis_arguments = sys.argv[sys.argv.index("--") + 1:]

histmaker_args, _ = parser.parse_known_args(analysis_arguments)

input_file = Path(histmaker_args.input_file)
output_file = Path(histmaker_args.output_file)

# FCCAnalyses histmaker configuration
processList = {
    input_file.stem: {
        "fraction": 1,
        "output": output_file.stem,
    }
}

inputDir = str(input_file.parent)
outputDir = str(output_file.parent)

procDict = "FCCee_procDict_winter2023_IDEA.json"

doScale = False
intLumi = 1.0


def build_graph(dframe, dataset, args):

    analysis = _Analysis(vars(args))

    weightsum = dframe.Count()

    dframe = analysis.analyzers(dframe)

    results = []


    for branch_name in analysis.output():
        results.append(
            dframe.Histo1D(
                (branch_name, "", 50, 0, 150),
                branch_name,
            )
        )

    return results, weightsum