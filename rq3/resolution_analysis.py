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
    fig, ax = plt.subplots(figsize=(10, 6))
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