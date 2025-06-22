import json
import os

import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def plot_total_category_pie(df, categories):
    category_total_conflicts = {cat: df[cat].sum() for cat in categories}
    total_conflicts_sum = sum(category_total_conflicts.values())

    # Create labels with percentages included
    labels = [
        f"{cat}\n{(count / total_conflicts_sum) * 100:.1f}\%"
        for cat, count in zip(["Major", "Minor", "Patch", "Other", "Invalid SemVer"], category_total_conflicts.values())
    ]

    fig, ax = plt.subplots(figsize=(5.6, 3.5))

    ax.set_facecolor("none")  # removes background inside plot area
    fig.patch.set_facecolor("none")  # removes background around the plot

    wedges, texts = ax.pie(
        category_total_conflicts.values(),
        labels=labels,
        labeldistance=1.33,
        startangle=36,
        colors=plt.cm.Set2.colors,
        wedgeprops={'edgecolor': 'black'},
        radius=0.75
    )

    # Set font size for labels
    for text in texts:
        text.set_fontsize(17)

    # ax.set_title(f"Semantic Differences in {total_conflicts_sum} Version Conflicts", fontsize=12)
    plt.tight_layout()
    # plt.show()
    plt.savefig("figures/pie_total_by_category.pgf")
    # plt.close()


def print_module_conflicts_summary_table(module_conflicts):
    module_conflicts_per_category = {
        "MAJOR": [],
        "MINOR": [],
        "PATCH": [],
        "OTHER": [],
        "INVALID_SEMVER": [],
        "TOTAL": []
    }

    for pr_url, modules in module_conflicts.items():
        for module, stats in modules.items():
            for category in module_conflicts_per_category.keys():
                count = stats.get(category, 0)
                module_conflicts_per_category[category].append(count)

    summary_data = []
    for category, counts in module_conflicts_per_category.items():
        summary_data.append({
            "Semantic Difference": category,
            "Min": min(counts),
            "Max": max(counts),
            "Median": np.median(counts),
            "Average": np.mean(counts),
            "Total": sum(counts)
        })

    # Create DataFrame
    summary_df = pd.DataFrame(summary_data)
    summary_df[["Median", "Average"]] = summary_df[["Median", "Average"]].round(2)

    # print summary_df without index
    print(summary_df.to_string(index=False))


def plot_category_conflicts_per_module_histogram(module_conflicts, category, bins):
    module_totals = []

    for pr_url, modules in module_conflicts.items():
        for module, stats in modules.items():
            module_totals.append(stats.get(category, 0))

    # Convert to DataFrame for convenience
    df = pd.DataFrame(module_totals, columns=["conflicts"])

    # Plotting
    data = df["conflicts"].dropna().values

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    sns.histplot(data, bins=bins, ax=ax, color='#7fc173', alpha=0.5,
                 edgecolor='black', linewidth=0.4)

    # Styling
    ax.set_xlabel(f"{category} Version Conflicts per Module", fontsize=11)
    ax.set_ylabel("Pull Requests", fontsize=11)
    ax.tick_params(axis='both', labelsize=10)

    # Vertical line for median
    median = np.median(data)
    ax.axvline(x=median, color='black', linestyle=(0, (5, 8)),
               linewidth=1, label=f"$\\tilde{{x}}$ = {median:.1f}")
    ax.legend(fontsize=11, loc='upper right')

    # Remove top and right borders
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Make sure output folder exists
    os.makedirs("figures", exist_ok=True)

    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        "text.usetex": True,
        "pgf.rcfonts": False,
        "font.size": 5,
    })
    # sns.set_theme(style="whitegrid", font_scale=0.2, rc={"grid.linewidth": 0.3})

    # Load your DataFrame
    df = pd.read_csv("../data/rq2_semantic_differences.csv")  # Replace with your actual DataFrame if loaded differently
    module_conflicts = json.load(open("semantic_differences_per_module.json", "r"))

    # Make sure the json file contains only PRs that are in the dataframe
    # keys_to_delete = [pr for pr in module_conflicts if pr not in df['pr_url'].values]
    #
    # # Then, delete them
    # for pr in keys_to_delete:
    #     print(pr)
    #     del module_conflicts[pr]
    #
    # json.dump(module_conflicts, open("semantic_differences_per_module.json", "w"), indent=4)

    print(f"{len(df)} PRs with semantic differences found")
    print(df[['affected_modules']].sum())
    print('\n')

    # Define your categories
    categories = ['major', 'minor', 'patch', 'other', 'invalid_semver']

    plot_total_category_pie(df, categories)
    print_module_conflicts_summary_table(module_conflicts)

    # plot_category_conflicts_per_module_histogram(module_conflicts, category="TOTAL", bins=80)
    # plot_category_conflicts_per_module_histogram(module_conflicts, category="MAJOR", bins=50)
    # plot_category_conflicts_per_module_histogram(module_conflicts, category="MINOR", bins=50)
    # plot_category_conflicts_per_module_histogram(module_conflicts, category="PATCH", bins=50)
