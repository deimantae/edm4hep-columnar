import awkward as ak
import uproot
import hist
from coffea import util
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Load histogram objects created from the input data
input_histograms = util.load("input_histograms.coffea")

# Read branches from the output RNTuple
with uproot.open("output.root") as output_file:
    rntuple = output_file["Events"]

    # Create output histograms
    output_histograms = {}

    for branch in rntuple.keys():
        # Filter internal RNTuple storage fields
        if "._" in branch:
            continue

        values = rntuple[branch].array()

        output_histograms[branch] = (
            hist.Hist.new
            .Reg(50, 0, 150)
            .Double()
            .fill(ak.ravel(values))
        )

# Compare input and output histograms
with PdfPages("histogram_comparison.pdf") as pdf:
    for branch in output_histograms:
        fig, ax = plt.subplots(figsize=(6, 4))

        input_histograms[branch].plot1d(
            ax=ax,
            label="Input",
            color="blue",
            linewidth=2,
        )

        output_histograms[branch].plot1d(
            ax=ax,
            label="Output",
            color="lightsteelblue",
            linewidth=2,
            linestyle="--",
        )

        ax.set_title(branch)
        ax.set_xlabel(branch)
        ax.set_ylabel("Entries")
        ax.legend()
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

print("Saved comparison to histogram_comparison.pdf")