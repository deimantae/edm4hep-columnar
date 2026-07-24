import awkward as ak
import uproot
import hist
import mplhep as hep
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
        values = rntuple[branch].array()

        output_histograms[branch] = (
            hist.Hist.new
            .Reg(50, 0, 150)
            .Double()
            .fill(ak.ravel(values))
        )
        
# Plot style
hep.style.use("ROOT")
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 14,
    "mathtext.fontset": "stix",
})

# Compare input and output histograms
with PdfPages("histogram_comparison.pdf") as pdf:
    for branch in output_histograms:
        input_hist = input_histograms[branch]
        output_hist = output_histograms[branch]
        
        fig, (ax, ax_difference) = plt.subplots(
            2,
            1,
            figsize=(6, 6),
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1],
                         "hspace": 0.08}
            )

        input_hist.plot1d(
            ax=ax,
            label=r"$h_1$",
            color="navy",
            linewidth=1.5
        )

        output_hist.plot1d(
            ax=ax,
            label=r"$h_2$",
            color="lightsteelblue",
            linewidth=1.5,
            linestyle="--"
        )
    
        # Difference panel
        difference = input_hist.values() - output_hist.values()
        
        ax_difference.axhline(
            0,
            color="lightsteelblue",
            linestyle="--",
            linewidth=1
            )

        ax_difference.plot(
            input_hist.axes[0].centers,
            difference,
            linestyle="none",
            marker="o",
            color="navy",
            markersize=3
            )
        
        ax.legend(frameon=False, loc="upper right")
        
        # Top panel 
        ax.set_ylabel("Entries")
        ax.tick_params(labelbottom=False)
        ax.xaxis.label.set_visible(False)
        
        # Bottom panel
        ax_difference.set_ylabel(r"$h_1-h_2$")
        ax_difference.set_xlabel(branch)
        
        # Center axis labels
        ax.yaxis.set_label_coords(-0.08, 0.5)
        ax_difference.yaxis.set_label_coords(-0.08, 0.7)
        
        # Ticks pointing inward
        for axis in (ax, ax_difference):
            for spine in axis.spines.values():
                spine.set_linewidth(1.0)
            
            axis.tick_params(
                direction="in",
                which="major",
                length=4,
                width=0.8,
                top=True,
                right=True
                )
            
            axis.tick_params(
                direction="in",
                which="minor",
                length=2,
                width=0.6,
                top=True,
                right=True
                )
            
            axis.minorticks_on()
        
        pdf.savefig(fig)
        plt.close(fig)

print("Saved comparison to histogram_comparison.pdf")