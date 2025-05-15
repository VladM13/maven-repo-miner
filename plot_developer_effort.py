import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = 'rq1_repositories_with_version_conflict_pulls.csv'


def create_boxplots(df, columns, plot_titles):
    """
    Create a vertical boxplot for each specified column in subplots.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the data.
    columns (list of str): Column names to plot.
    plot_titles (list of str): Titles for each subplot.
    """
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 6), sharey=False)

    for ax, col, title in zip(axes, columns, plot_titles):
        sns.boxplot(y=df[col].dropna(), ax=ax)
        ax.set_title(title)
        ax.set_ylabel(col)
        ax.locator_params(axis='y', nbins=10)

    plt.tight_layout()
    plt.show()

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
    # df = pd.read_csv("../use_freq.csv")
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

    create_boxplots(df, columns, titles)


if __name__ == "__main__":
    main()
