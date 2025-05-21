import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = '../data/final_version_conflict_prs.csv'


def create_boxplots(df, columns, labels):
    fig, axes = plt.subplots(nrows=1, ncols=len(columns), figsize=(5.5, 2.5), sharey=False)

    if len(columns) == 1:
        axes = [axes]

    for ax, col, label in zip(axes, columns, labels):
        data = df[col].dropna().values

        # Violin plot
        parts = ax.violinplot([data], showmeans=False, showmedians=False, showextrema=False)
        for pc in parts['bodies']:
            pc.set_facecolor('#c1ece6')
            pc.set_edgecolor('black')
            pc.set_alpha(0.5)

        # Boxplot
        box = ax.boxplot([data], showfliers=False, widths=0.3, patch_artist=True)
        for patch in box['boxes']:
            patch.set(facecolor='white', edgecolor='black', linewidth=0.6)
        box['medians'][0].set(color='#dd2424', linewidth=0.6)
        for element in ['whiskers', 'caps']:
            for item in box[element]:
                item.set(color='black', linewidth=0.6)

        ax.set_title(label, fontsize=8)
        ax.set_xlabel(f"$\\mu$ = {data.mean():.1f}, $\\tilde{{x}}$ = {np.median(data):.1f}", fontsize=8)
        ax.tick_params(axis='y', labelsize=7, pad=-3)
        ax.set_xticks([])

        # Remove spines for cleaner academic look
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    # plt.suptitle("Developer Effort Metrics", fontsize=8)
    plt.tight_layout()
    plt.savefig("figures/boxplots.pgf")


def create_histograms(df, col, plot_title, x_axis_label, bins):
    data = df[col].dropna().values

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    sns.histplot(data, bins=bins, ax=ax, color='#7fc173', alpha=0.5, edgecolor='black', linewidth=0.4)

    # ax.set_title(plot_title, fontsize=8)
    ax.set_xlabel(x_axis_label, fontsize=11)
    ax.set_ylabel("Pull Requests", fontsize=11)
    ax.tick_params(axis='both', labelsize=10)

    ax.axvline(x=0, color='black', linestyle=(0,(5, 8)), linewidth=1, label='Mean')
    ax.legend(fontsize=11, loc='upper right')

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"figures/histogram_{col}.pgf")

    less_than_average = np.count_nonzero(df[col] < 0)
    print(f"{less_than_average}/{len(data)} PRs ({less_than_average / len(data) * 100:.2f}%) are below the mean of {col}")


def main():
    # Configure LaTeX rendering and theme
    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        "text.usetex": True,
        "pgf.rcfonts": False,
        "font.size": 5,
    })
    sns.set_theme(style="whitegrid", font_scale=0.2, rc={"grid.linewidth": 0.3})

    df = pd.read_csv(INPUT_CSV)

    columns = ['no_of_comments', 'time_to_merge', 'java_code_changes', 'time_from_detection_to_resolution']
    labels = ['(a) Comments', '(b) Merge Time (hours)', '(c) Java Code Line\n Changes', '(d) Detection to\n Resolution Time (hours)']

    create_boxplots(df, columns, labels)
    create_histograms(df, 'time_to_merge_normalized', "Distribution of Normalized Merge Times", "Normalized Merge Time (z-score)", 30)
    create_histograms(df, 'no_of_comments_normalized', "Distribution of Normalized Comments", "Normalized Comments (z-score)", 45)


if __name__ == "__main__":
    main()
