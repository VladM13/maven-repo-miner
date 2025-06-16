from collections import Counter
import pandas as pd

INPUT_CSV = '../data/final_version_conflict_prs.csv'
OUTPUT_CSV = 'rq3_resolution_strategies.csv'


def main():
    df = pd.read_csv(INPUT_CSV)

    # Check if 'resolution_strategy' exists in the DataFrame
    if 'resolution_strategy' not in df.columns:
        print(f"'resolution_strategy' column not found in {INPUT_CSV}.")
        return

    # Count the occurrences of each resolution strategy
    all_strategies = df['resolution_strategy'].dropna().apply(lambda x: [s.strip() for s in x.split(',')])
    flat_list = [strategy for sublist in all_strategies for strategy in sublist]
    resolution_counts = Counter(flat_list)
    resolution_counts = pd.Series(resolution_counts).sort_values(ascending=False)

    # Print the counts
    print("Resolution Strategy Counts:")
    for strategy, count in resolution_counts.items():
        print(f"{strategy}: {count}")

    # Save the counts to a new CSV file
    resolution_counts.to_csv(OUTPUT_CSV, header=True)
    print(f"Counts saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()