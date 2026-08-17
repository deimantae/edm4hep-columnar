"""
Compare two ROOT histogram files

This script can be run directly or imported by edm4hep_columnar.py
"""

from argparse import ArgumentParser

import matplotlib.pyplot as plt
import ROOT

from matplotlib.backends.backend_pdf import PdfPages


def compare_histograms(
    histograms_1_path,
    histograms_2_path,
    output_file="histogram_comparison.pdf",
):

    # Open histogram files
    histograms_1 = ROOT.TFile.Open(histograms_1_path, "READ")
    histograms_2 = ROOT.TFile.Open(histograms_2_path, "READ")
    print("Comparing histograms...\n")

    # Count different histograms for validation
    different = 0

    # Plot style
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 14,
        "mathtext.fontset": "stix",
    })

    # Compare histograms
    with PdfPages(output_file) as pdf:
        for key in histograms_2.GetListOfKeys():
            branch = key.GetName()

            histogram_1 = histograms_1.Get(branch)
            histogram_2 = histograms_2.Get(branch)

            # Check if no histograms are missing from either file
            if not histogram_1 or not histogram_2:
                print(f"{branch:.<30} missing")
                different += 1
                continue

            bin_centers = []
            values_1 = []
            values_2 = []

            for bin_index in range(1, histogram_1.GetNbinsX() + 1):
                bin_centers.append(histogram_1.GetBinCenter(bin_index))

                values_1.append(histogram_1.GetBinContent(bin_index))
                values_2.append(histogram_2.GetBinContent(bin_index))

            # Difference panel
            difference = []

            for value_1, value_2 in zip(values_1, values_2):
                difference.append(value_1 - value_2)

            # Validation
            if all(value == 0 for value in difference):
                print(f"{branch:.<30} identical")
            else:
                print(f"{branch:.<30} different")
                different += 1

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

            histogram_1_label = r"$h_1$"
            histogram_2_label = r"$h_2$"

            ax.step(
                bin_centers,
                values_1,
                where="mid",
                label=histogram_1_label,
                color="navy",
                linewidth=1.5
            )

            ax.step(
                bin_centers,
                values_2,
                where="mid",
                label=histogram_2_label,
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

    number_histograms = histograms_2.GetListOfKeys().GetSize()

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

    histograms_1.Close()
    histograms_2.Close()

    print(f"Saved comparison to {output_file}")


def main():
    parser = ArgumentParser(description="Compare two ROOT histogram files")
    parser.add_argument("histograms_1", help="First histogram file")
    parser.add_argument("histograms_2", help="Second histogram file")
    parser.add_argument("--output-file", default="histogram_comparison.pdf",
                        help="Output PDF file")

    args = parser.parse_args()
    compare_histograms(args.histograms_1, args.histograms_2, args.output_file)


# Allow this file to be imported by edm4hep_columnar.py
# without executing the CLI
if __name__ == "__main__":
    main()
