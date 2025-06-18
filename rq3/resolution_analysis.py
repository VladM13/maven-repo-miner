from collections import Counter
import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

INPUT_CSV = '../data/final_version_conflict_prs.csv'
OUTPUT_CSV = 'rq3_resolution_strategies.csv'


def extract_resolution_strategies_to_csv(df):
    all_strategies = df['resolution_strategy'].dropna().apply(lambda x: [s.strip() for s in x.split(',')])
    flat_list = [strategy for sublist in all_strategies for strategy in sublist]
    resolution_counts = Counter(flat_list)
    resolution_counts = pd.Series(resolution_counts).sort_values(ascending=False)
    resolution_counts = resolution_counts.rename_axis("resolution_strategy").reset_index(name="frequency")
    # Save the counts to a new CSV file
    resolution_counts.to_csv(OUTPUT_CSV, header=True, index=False)
    print(f"Counts saved to {OUTPUT_CSV}")
    return resolution_counts


def plot_category_barplot(category_df):
    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        "text.usetex": True,
        "pgf.rcfonts": False,
        "font.size": 5,
    })
    sns.set_theme(style="whitegrid", font_scale=0.2, rc={"grid.linewidth": 0.3})

    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    order = category_df.sort_values(by='Category')['Category']
    sns.barplot(data=category_df, x="PRs", y="Category", palette="deep", ax=ax, order=order)
    ax.set_xlabel("PRs", fontsize=16)
    ax.set_ylabel("Resolution Category", fontsize=16)
    ax.tick_params(axis='both', labelsize=16)
    ax.tick_params(axis='y', pad=15)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"figures/resolution_categories.pgf")


def plot_metric_boxplots_by_category(conflicts_per_category, categories):
    metrics = ['comments', 'time_to_merge', 'java_code_changes']
    metric_labels = {
        'comments': 'Number of Comments',
        'time_to_merge': 'Time to Merge (hours)',
        'java_code_changes': 'Java Code Changes'
    }

    for metric in metrics:
        data = [conflicts_per_category[cat_idx][metric] for cat_idx in sorted(categories.keys())]

        fig, ax = plt.subplots(figsize=(8, 4))
        box = ax.boxplot(data, patch_artist=True, showfliers=True,
                         flierprops=dict(marker='o', markeredgecolor='black', markersize=4, alpha=0.5))

        ax.set_title(f'{metric_labels[metric]} by Resolution Strategy Category')
        ax.set_ylabel(metric_labels[metric])
        ax.set_xticks(range(1, len(categories) + 1))
        ax.set_xticklabels([categories[i] + f" ({len(conflicts_per_category[i][metric])} PRs)" for i in sorted(categories.keys())], rotation=30, ha='right')
        ax.tick_params(axis='both', labelsize=9)
        plt.tight_layout()
        plt.savefig(f"figures/{metric}_by_category.png")


def analyze_effort_per_resolution_category(categories, df, resolution_counts_df):
    conflicts_per_category = {}

    for category in categories.keys():
        conflicts_per_category[category] = {'comments': [], 'time_to_merge': [], 'java_code_changes': []}

    for index, row in df.iterrows():
        strategies = [s.strip() for s in row['resolution_strategy'].split(',')]
        for strategy in strategies:
            if strategy in resolution_counts_df['resolution_strategy'].values:
                strategy_category = \
                resolution_counts_df.loc[resolution_counts_df['resolution_strategy'] == strategy].get('category',
                                                                                                      None).values[0]
                strategy_category = int(strategy_category)
                conflicts_per_category[strategy_category]['comments'].append(row['comments'])
                conflicts_per_category[strategy_category]['time_to_merge'].append(row['time_to_merge'])
                conflicts_per_category[strategy_category]['java_code_changes'].append(row['java_code_changes'])

    plot_metric_boxplots_by_category(conflicts_per_category, categories)


def main():
    df = pd.read_csv(INPUT_CSV)

    # Check if 'resolution_strategy' exists in the DataFrame
    if 'resolution_strategy' not in df.columns:
        print(f"'resolution_strategy' column not found in {INPUT_CSV}.")
        return

    # Count the occurrences of each resolution strategy
    mixed_strategies = 0
    for index, row in df.iterrows():
        if "," in row['resolution_strategy']:
            mixed_strategies += 1

    print(f"{mixed_strategies}/{len(df)} PRs ({mixed_strategies/len(df) * 100:.2f}%) with mixed resolution strategies: ")

    # resolution_counts = extract_resolution_strategies_to_csv(df)
    resolution_counts_df = pd.read_csv(OUTPUT_CSV)

    categories = {
        1: "I. Controlling dependency versions locally",
        2: "II. Managing dependency versions centrally",
        3: "III. Managing transitive dependencies",
        4: "IV. Removing or replacing dependencies",
        5: "V. Shading dependencies",
        6: "VI. Other"
    }

    # analyze_effort_per_resolution_category(categories, df, resolution_counts_df)

    # Count strategies per category
    category_counts = Counter()
    for index, row in resolution_counts_df.iterrows():
        category_counts[categories[row['category']]] += row['frequency']

    # Create DataFrame for plotting
    category_df = pd.Series(category_counts).sort_values().reset_index()
    category_df.columns = ["Category", "PRs"]

    plot_category_barplot(category_df)


if __name__ == "__main__":
    main()