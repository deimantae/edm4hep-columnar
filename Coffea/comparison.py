"""
Compare two ROOT histogram files

This script can be run directly or imported by edm4hep_columnar.py
"""

from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np
import uproot

from matplotlib.backends.backend_pdf import PdfPages


def compare_histograms(
    histograms_1_path,
    histograms_2_path,
    output_file="histogram_comparison.pdf"
):

    # Open histogram files
    histograms_1 = uproot.open(histograms_1_path)
    histograms_2 = uproot.open(histograms_2_path)
    print("Comparing histograms...\n")

    # Count different histograms for validation
    different = 0

    # Get histogram names from both files
    branches_1 = set(histograms_1.keys(cycle=False))
    branches_2 = set(histograms_2.keys(cycle=False))
    branches = sorted(branches_1 | branches_2) # combine names from both files

    # Plot style
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 14,
        "mathtext.fontset": "stix"
    })

    # Compare histograms
    with PdfPages(output_file) as pdf:
        for branch in branches:

            # Check if histograms are missing from either file
            if branch not in branches_1 or branch not in branches_2:
                print(f"{branch:.<30} missing")
                different += 1
                continue

            histogram_1 = histograms_1[branch]
            histogram_2 = histograms_2[branch]

            # Get bin contents and binning
            bin_centers = histogram_1.axis().centers()
            bin_edges_1 = histogram_1.axis().edges()
            bin_edges_2 = histogram_2.axis().edges()

            values_1 = histogram_1.values()
            values_2 = histogram_2.values()

            # Different binning cannot be compared bin by bin
            if (
                len(bin_edges_1) != len(bin_edges_2)
                or not np.allclose(bin_edges_1, bin_edges_2)
            ):
                print(f"{branch:.<30} different binning")
                different += 1
                continue

            # Calculate bin-by-bin difference
            difference = values_1 - values_2

            # Validation
            # Allow one entry bin shifts caused by float32 rounding differences
            # when comparing Coffea and FCCAnalyses
            if np.allclose(values_1, values_2, rtol=0, atol=1):
                print(f"{branch:.<30} identical")
            else:
                print(f"{branch:.<30} different")
                different += 1

            # Plot histogram comparison
            fig, (ax, ax_difference) = plt.subplots(
                2,
                1,
                figsize=(6, 6),
                sharex=True,
                gridspec_kw={
                    "height_ratios": [3, 1],
                    "hspace": 0.08
                },
            )

            ax.step(
                bin_centers,
                values_1,
                where="mid",
                label=r"$h_1$",
                color="navy",
                linewidth=1.5
            )

            ax.step(
                bin_centers,
                values_2,
                where="mid",
                label=r"$h_2$",
                color="lightsteelblue",
                linewidth=1.5,
                linestyle="--"
            )

            ax_difference.axhline(
                0,
                color="lightsteelblue",
                linestyle="--",
                linewidth=1
            )

            ax_difference.plot(
                bin_centers,
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
            ax.yaxis.set_label_coords(-0.13, 0.5)
            ax_difference.yaxis.set_label_coords(-0.13, 0.5)

            # More space for y axis labels
            fig.subplots_adjust(left=0.18)

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

    number_histograms = len(branches)

    if different == 0:
        print(
            f"\nValidation successful: all {number_histograms} "
            "histograms are identical."
        )
    else:
        print(
            f"\nValidation failed: {different} of {number_histograms} "
            "histograms differ."
        )

    histograms_1.close()
    histograms_2.close()

    print(f"Saved comparison to {output_file}")


def main():
    parser = ArgumentParser(description="Compare two ROOT histogram files")
    parser.add_argument("histograms_1", help="First histogram file")
    parser.add_argument("histograms_2", help="Second histogram file")
    parser.add_argument(
        "--output-file",
        default="histogram_comparison.pdf",
        help="Output PDF file"
    )

    args = parser.parse_args()
    compare_histograms(
        args.histograms_1,
        args.histograms_2,
        args.output_file
    )


# Allow this file to be imported by edm4hep_columnar.py
# without executing the CLI
if __name__ == "__main__":
    main()
