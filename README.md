# Repository Miner for Maven Version Conflicts

This project was used to support an empirical study on version conflicts in Maven-based Java projects, as part of the
[CSE3000: Research Project 2024/25](https://github.com/TU-Delft-CSE/Research-Project) course at TU Delft. It uses the GitHub API to mine Java repositories on GitHub for Maven version conflicts. 

The paper is available [here](https://resolver.tudelft.nl/uuid:767614b7-ba68-4cba-a490-b42f5d226cea).

## Installation
To run this project, you will need to have Python 3.10 or higher installed on your machine.

Install the required packages by running the following command in your terminal:

```bash
pip install -r requirements.txt
```

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file/PyCharm run
configuration

`GITHUB_TOKEN` -
Your [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
used to access the GitHub API. 

## File Structure
```
├── data
│   ├── final_version_conflict_prs.csv                              # dataset of 124 version conflict PRs identified through manual inspection    
│   ├── initial_version_conflict_prs.csv                            # dataset of 196 PRs identified through keyword search with GitHub API
│   ├── java_repos_from_April_2015_min_50_stars_min_50_issues.csv   # dataset of 5,919 Java repositories
│   ├── rq2_final_version_conflict_overview.csv                     # overview of 85 version conflict PRs manually reviewed in RQ2
│   └── rq2_semantic_differences.csv                                # overview of semantic differences between version conflicts in 70 PRs
├── data-collection
│   ├── filter_repo_population.py                                   # script to filter the initial repository population
│   ├── pr_mining.py                                                # script for keyword search to find PRs related to version conflicts
│   └── repo_statistics.py                                          # script to collect demographics about the repositories
├── rq1
│   ├── comments_cache.json                                         # cache of comment means and std in 69 Java repositories
│   ├── developer_effort_basic_metrics.py                           # script to compute basic developer effort metrics based on PR activity
│   ├── developer_effort_normalized_metrics.py                      # script to compute normalized number of comments and merge time
│   ├── merge_times_cache.json                                      # cache of merge times in 85 Java repositories
│   └── plot_developer_effort.py                                    # script to plot developer effort metrics
├── rq2
│   ├── compute_semantic_difference.py                              # script to compute semantic differences between version conflicts
│   ├── detect_conflicting_versions.py                              # script to detect conflicting versions in PRs
│   ├── plot_semantic_differences.py                                # script to plot semantic differences between version conflicts
│   └── semantic_differences_per_module.json                        # cache of semantic differences per module in 70 version conflict PRs
└── rq3
    ├── resolution_analysis.py                                      # script to plot resolution strategies in version conflict PRs
    ├── resolution_categories.txt                                   # text file with resolution categories classification
    └── rq3_resolution_strategies.csv                               # overview of resolution strategies in 124 version conflict PRs
```    

