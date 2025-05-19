import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = '../data/final_version_conflict_prs.csv'


def create_boxplots(df, columns, labels, output_path='boxplots.pgf'):
    """
    Create subplots with violin + boxplots for each column using LaTeX rendering.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the data.
    columns (list of str): Column names to plot.
    plot_titles (list of str): Titles for each subplot.
    output_path (str): File path to save the PGF figure.
    """

    fig, axes = plt.subplots(nrows=1, ncols=len(columns), figsize=(10, 5), sharey=False)

    if len(columns) == 1:
        axes = [axes]  # make iterable if only one subplot

    for ax, col, label in zip(axes, columns, labels):
        data = df[col].dropna().values
        ax.violinplot([data], showmeans=False, showmedians=False, showextrema=False)
        ax.boxplot([data], showfliers=False, widths=[0.4])
        ax.set_title(label, fontsize=12)
        ax.set_xlabel(f"Mean = {data.mean():.2f}\n Median = {np.median(data):.2f}", fontsize=12)
        # ax.set_ylabel(label, fontsize=12)
        ax.set_xticks([])

    plt.suptitle("Developer Effort Metrics", fontsize=15)
    plt.tight_layout()
    # plt.savefig(output_path)
    plt.show()


def main():
    df = pd.read_csv(INPUT_CSV)

    columns = ['no_of_comments', 'time_to_merge', 'java_code_changes', 'time_from_detection_to_resolution']
    labels = ['Number of Comments', 'Time to Merge (h)', 'Java Code Line Changes', 'Detection to Resolution\n Time (n=31)']

    # Enable LaTeX via PGF
    # matplotlib.use("pgf")
    # matplotlib.rcParams.update({
    #     "pgf.texsystem": "pdflatex",
    #     'font.family': 'serif',
    #     'font.size': 7,
    #     'text.usetex': True,
    #     'pgf.rcfonts': False,
    #     'axes.labelsize': 'small',
    #     'axes.titlesize': 'medium',
    # })

    create_boxplots(df, columns, labels)

    # create_histograms(df)
    less_than_average_merge_time = np.count_nonzero(df['time_to_merge_normalized'] < 0)
    print(f"{less_than_average_merge_time} PRs ({less_than_average_merge_time / len(df) * 100:.2f}%) are below the mean merge time")

def create_histograms(df):
    data = df['time_to_merge_normalized'].dropna().values

    # Create a histogram for the normalized merge times
    sns.histplot(data, bins=30)
    plt.title("Distribution of Normalized Merge Times", fontsize=15)
    plt.xlabel("Normalized Merge Time (z-score)", fontsize=12)
    plt.ylabel("Pull Requests", fontsize=12)
    plt.axvline(x=0, color='gray', linestyle='--', label='Mean')
    plt.legend(fontsize=12)
    plt.tight_layout()
    # plt.savefig("histogram_time_to_merge_normalized.pgf")
    plt.show()


if __name__ == "__main__":
    main()
