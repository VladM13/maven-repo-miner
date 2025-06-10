import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator

INPUT_CSV = '../data/final_version_conflict_prs.csv'


def create_boxplot(df, columns, figname):
    fig, ax = plt.subplots(figsize=(1.5, 2))

    data = [df[col].dropna().values for col in columns]

    # Violin plot
    parts = ax.violinplot(data, showmeans=False, showmedians=False, showextrema=False)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor('#c1ece6')
        pc.set_edgecolor('black')
        pc.set_alpha(0.5)

    # Boxplot
    box = ax.boxplot(data, showfliers=False, widths=0.3, patch_artist=True)
    for patch in box['boxes']:
        patch.set(facecolor='white', edgecolor='black', linewidth=0.6)
    for median in box['medians']:
        median.set(color='#dd2424', linewidth=0.6)
    for element in ['whiskers', 'caps']:
        for item in box[element]:
            item.set(color='black', linewidth=0.6)

    ax.set_xticks([])
    ax.tick_params(axis='y', labelsize=8, pad=-3)

    # Optionally: show medians as x-axis labels
    medians = [np.median(d) for d in data]
    ax.set_xlabel(" | ".join(f"$\\tilde{{x}}$ = {med:.1f}" for col, med in zip(columns, medians)),
                  fontsize=9)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"figures/{figname}.pgf")


def create_histograms(df, col, x_axis_label, bins):
    data = df[col].dropna().values

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    sns.histplot(data, bins=bins, ax=ax, color='#7fc173', alpha=0.5, edgecolor='black', linewidth=0.4)

    ax.set_ylabel("PRs", fontsize=14)
    ax.tick_params(axis='both', labelsize=14)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.axvline(x=0, color='black', linestyle=(0,(5, 8)), linewidth=1.5, label='Mean')
    ax.legend(fontsize=14, loc='upper right')

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

    create_boxplot(df, columns=['comments'], figname='developer_effort_metrics_a')
    create_boxplot(df, columns=['pure_comments'], figname='developer_effort_metrics_b')
    print(f"{df['pure_comments'].sum()}/{df['comments'].sum()} comments ({df['pure_comments'].sum() / df['comments'].sum() * 100:.2f}%) are pure (excluding comments for running bot commands and comments created by bots)")

    create_boxplot(df, columns=['time_to_merge'], figname='developer_effort_metrics_c')
    create_boxplot(df, columns=['java_code_changes'], figname='developer_effort_metrics_d')
    create_boxplot(df, columns=['time_from_detection_to_resolution'], figname='developer_effort_metrics_e')


    create_histograms(df, 'time_to_merge_normalized', "Normalized Merge Time (z-score)", 30)
    create_histograms(df, 'comments_normalized', "Normalized Comments (z-score)", 35)

    print(f"{len(df[df['comments_normalized'].notnull()]['repository'].unique())} repositories in the normalized comments dataset")

if __name__ == "__main__":
    main()
