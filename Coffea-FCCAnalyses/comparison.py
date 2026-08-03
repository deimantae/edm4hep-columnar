'''
Compare two histogram files.

This script can be run directly or imported by edm4hep_reduce.py
'''

from argparse import ArgumentParser

import matplotlib.pyplot as plt
import mplhep as hep

from coffea import util
from matplotlib.backends.backend_pdf import PdfPages


def compare_histograms(
    histograms_1_path, histograms_2_path,
    output_file="histogram_comparison.pdf"
    ):
    
    # Load histogram objects
    histograms_1 = util.load(histograms_1_path)
    histograms_2 = util.load(histograms_2_path)
        
    # Plot style
    hep.style.use("ROOT")
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 14,
        "mathtext.fontset": "stix",
    })
    
    # Compare input and output histograms
    with PdfPages(output_file) as pdf:
        for branch in histograms_2:
            histogram_1 = histograms_1[branch]
            histogram_2 = histograms_2[branch]
            
            fig, (ax, ax_difference) = plt.subplots(
                2,
                1,
                figsize=(6, 6),
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1],
                             "hspace": 0.08}
                )
    
            histogram_1.plot1d(
                ax=ax,
                label=r"$h_1$",
                color="navy",
                linewidth=1.5
            )
    
            histogram_2.plot1d(
                ax=ax,
                label=r"$h_2$",
                color="lightsteelblue",
                linewidth=1.5,
                linestyle="--"
            )
        
            # Difference panel
            difference = histogram_1.values() - histogram_2.values()
            
            ax_difference.axhline(
                0,
                color="lightsteelblue",
                linestyle="--",
                linewidth=1
                )
    
            ax_difference.plot(
                histogram_1.axes[0].centers,
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
    
    print(f"Saved comparison to {output_file}")
    

# Parse command-line arguments and run the comparison
# when this file is executed directly
    
def main():
    # Command-line arguments
    parser = ArgumentParser(description="Compare two histogram files")
    parser.add_argument("histograms_1", help="First histogram file")
    parser.add_argument("histograms_2", help="Second histogram file")
    parser.add_argument("--output-file", default="histogram_comparison.pdf",
    help="Output PDF file.")

    args = parser.parse_args()
    
    compare_histograms(args.histograms_1, args.histograms_2, args.output_file)

# Allow this file to be imported by edm4hep_reduce.py
# without executing the CLI
if __name__ == "__main__":
    main()