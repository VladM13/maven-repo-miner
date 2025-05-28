import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def create_total_category_histogram(df, categories):
    totals = {cat: df[cat].sum() for cat in categories}

    fig, ax = plt.subplots(figsize=(6, 3.0))
    sns.barplot(x=list(totals.keys()), y=list(totals.values()), palette='Set2', edgecolor='black')

    ax.set_xlabel("SemVer Difference", fontsize=11)
    ax.set_ylabel("Version Conflicts", fontsize=11)
    ax.tick_params(axis='both', labelsize=10)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()
    # plt.savefig("figures/histogram_total_by_category.pgf")
    plt.close()


def create_average_diff_per_module_boxplots(df, columns, labels, figname):
    fig, axes = plt.subplots(nrows=1, ncols=len(columns), figsize=(5.5, 2.5), sharey=True)

    if len(columns) == 1:
        axes = [axes]

    for ax, col, label in zip(axes, columns, labels):
        data = df[col].dropna().values
        data = data / df["num_modules"]  # Normalize by number of modules

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
        ax.set_xlabel(f"$\\tilde{{x}}$ = {np.median(data):.1f}", fontsize=8)
        ax.tick_params(axis='y', labelsize=7, pad=0)
        ax.set_xticks([])

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    axes[0].set_ylabel("Avg SemVer Difference per Module", fontsize=8)
    plt.tight_layout()
    plt.show()
    plt.close()
    # plt.savefig(f"figures/{figname}.pgf")


if __name__ == "__main__":
    # Make sure output folder exists
    os.makedirs("figures", exist_ok=True)

    # Load your DataFrame
    df = pd.read_csv("semantic_differences.csv")  # Replace with your actual DataFrame if loaded differently

    print(df[['num_modules', 'total', 'major', 'minor', 'patch', 'other', 'invalid_semver']].sum())

    # Define your categories
    categories = ['major', 'minor', 'patch', 'other', 'invalid_semver']

    # Call the plotting functions
    create_total_category_histogram(df, categories)
    create_average_diff_per_module_boxplots(df, categories, ["Major", "Minor", "Patch", "Other", "Invalid SemVer"], "average_diff_per_module")
