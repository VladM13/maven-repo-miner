import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = 'rq1_repositories_with_version_conflict_pulls.csv'


def create_boxplots(df, columns, plot_titles, output_path='boxplots.pgf'):
    """
    Create subplots with violin + boxplots for each column using LaTeX rendering.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the data.
    columns (list of str): Column names to plot.
    plot_titles (list of str): Titles for each subplot.
    output_path (str): File path to save the PGF figure.
    """
    # Enable LaTeX via PGF
    # matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        'font.family': 'serif',
        'font.size': 7,
        'text.usetex': True,
        'pgf.rcfonts': False,
        'axes.labelsize': 'small',
        'axes.titlesize': 'medium',
    })

    fig, axes = plt.subplots(nrows=1, ncols=len(columns), figsize=(3.4, 2), sharey=False)

    if len(columns) == 1:
        axes = [axes]  # make iterable if only one subplot

    for ax, col, title in zip(axes, columns, plot_titles):
        data = df[col].dropna().values
        ax.violinplot([data], showmeans=False, showmedians=False, showextrema=False)
        ax.boxplot([data], showfliers=False)
        ax.set_title(title)
        ax.set_ylabel("Value")
        ax.set_xticks([])

    plt.tight_layout()
    plt.show()
    # plt.savefig(output_path)


# def create_boxplots(df, columns, plot_titles):
#     """
#     Create a vertical boxplot for each specified column in subplots.
#
#     Parameters:
#     df (pd.DataFrame): The DataFrame containing the data.
#     columns (list of str): Column names to plot.
#     plot_titles (list of str): Titles for each subplot.
#     """
#     fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 6), sharey=False)
#
#     for ax, col, title in zip(axes, columns, plot_titles):
#         plt.violinplot(df[col].dropna())
#         ax.set_title(title)
#         ax.set_ylabel(col)
#         ax.locator_params(axis='y', nbins=10)
#
#     plt.tight_layout()
#     plt.show()

    # matplotlib.use("pgf")
    # matplotlib.rcParams.update({
    #     "pgf.texsystem": "pdflatex",
    #     'font.family': 'serif',
    #     'text.usetex': True,
    #     'pgf.rcfonts': False,
    #     'axes.labelsize': 'small',
    #     'axes.titlesize': 'medium',
    # })
    #
    # grouped = df.groupby('position')['usage'].apply(
    #     lambda x: x.values).sort_index().to_numpy()
    #
    # plt.figure(figsize=(3.4, 2.55))
    # plt.violinplot(grouped[1:6],
    #                positions=range(2, 7),
    #                showmeans=False,
    #                showmedians=False,
    #                showextrema=False)
    # plt.boxplot(grouped[1:6], positions=range(2, 7), showfliers=False)
    # plt.xlabel("Frequency Rank Within Family")
    # plt.ylabel("Normalized Usage Frequency")
    # plt.title("Usage Rate of Dependencies Across Families\nby Frequency Rank",
    #           wrap=True)
    # plt.tight_layout()
    # plt.savefig('../3_1.pgf')


def main():
    df = pd.read_csv(INPUT_CSV)

    columns = ['no_of_comments', 'time_to_merge', 'time_from_detection_to_resolution']
    titles = ['Number of Comments', 'Time to Merge', 'Detection to Resolution Time']

    # create_boxplots(df, columns, titles)

    sns.histplot(df['time_to_merge_normalized'], bins=30, kde=True)
    plt.title("Distribution of Normalized Merge Times")
    plt.xlabel("Normalized Merge Time (z-score)")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
