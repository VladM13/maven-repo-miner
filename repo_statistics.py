import pandas as pd

# In the run configuration, you need to set the GITHUB_TOKEN environment variable to your GitHub Personal Access Token
INPUT_CSV = 'data/final_version_conflict_prs.csv'
ALL_REPOS_CSV = 'data/java_repos_from_April_2015_min_50_stars_min_50_issues.csv'


def print_statistics(df, columns):
    stats = df[columns].describe().T
    stats['median'] = df[columns].median()
    print(stats[['min', 'max', 'median']].round(2))


def main():
    df = pd.read_csv(INPUT_CSV)
    all_repos_df = pd.read_csv(ALL_REPOS_CSV)

    repos = df['repository'].unique()
    selected_repos_df = all_repos_df[all_repos_df['name'].isin(repos)]

    print(f"Statistics for {len(repos)} selected repositories:")
    print_statistics(selected_repos_df, ['codeLines', 'commits', 'totalPullRequests', 'stargazers', 'contributors'])


if __name__ == "__main__":
    main()