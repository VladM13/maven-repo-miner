import os
import time
import json
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from rq1.developer_effort_basic_metrics import get_pr_reviews_count

# In the run configuration, set the GITHUB_TOKEN environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INPUT_CSV = 'rq1_repositories_with_version_conflict_pulls.csv'
OUTPUT_CSV = 'new_rq1_repositories_with_version_conflict_pulls.csv'

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

RATE_LIMIT_SLEEP = 60


def safe_get(url, headers, max_retries=5):
    """Make a GET request to the GitHub API with rate limit handling."""

    for i in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        elif response.status_code == 403:
            wait = 2 ** i
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)
        else:
            print(f"Request failed: {response.status_code} - {response.text}")
            break

    return None


def concurrent_get_normalized_time_to_merge(df, unique_repos, cache_file):
    """Fetch and normalize the time to merge for pull requests in all repositories."""

    def get_repo_pr_merge_times(repo_full_name):
        """Fetch the merge times of all pull requests for a given repository."""

        url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=closed&per_page=100"
        pr_merge_times = []

        while url:
            response = safe_get(url, HEADERS)
            if not response:
                # possibly reached rate limit
                return None

            prs = response.json()
            for pr in prs:
                if pr.get("merged_at"):
                    created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                    merged_at = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
                    merge_time = (merged_at - created_at).total_seconds() / 3600  # in hours
                    pr_merge_times.append(merge_time)

            # Pagination
            if 'link' in response.headers:
                next_link = None
                links = response.headers['link'].split(',')
                for link in links:
                    if 'rel="next"' in link:
                        next_link = link[link.find('<') + 1: link.find('>')]
                        break
                url = next_link
            else:
                url = None

        return pr_merge_times

    def fetch_merge_stats(repo_full_name):
        """Fetch merge time statistics for a given repository."""

        try:
            times = get_repo_pr_merge_times(repo_full_name)
            if len(times) > 1:
                merge_mean = float(np.mean(times))
                merge_std = float(np.std(times))
                print(f"Fetched {repo_full_name}: merged_prs={len(times)}, mean={merge_mean}, std={merge_std}")

                return repo_full_name, merge_mean, merge_std
        except Exception as e:
            print(f"Failed for {repo_full_name}: {e}")
        return repo_full_name, None, None

    repo_pr_avg_merge_time = {}
    repo_pr_stdev_merge_time = {}

    # Load cache if it exists
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)

        # Fill in from cache first
        for repo in unique_repos:
            if repo in cache:
                repo_pr_avg_merge_time[repo] = cache[repo]['mean']
                repo_pr_stdev_merge_time[repo] = cache[repo]['std']
    else:
        cache = {}

    # Fetch missing repositories
    to_fetch = [repo for repo in unique_repos if repo not in cache]

    if len(to_fetch) > 0:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(fetch_merge_stats, to_fetch))

        for repo, mean, std in results:
            if mean is not None:
                repo_pr_avg_merge_time[repo] = mean
                repo_pr_stdev_merge_time[repo] = std
                cache[repo] = {'mean': mean, 'std': std}

        # Save updated cache
        with open(cache_file, 'w') as f:
            json.dump(cache, f)

        # Update normalized time_to_merge column
        for index, row in df.iterrows():
            try:
                repo = row['repository']
                time_to_merge = row['time_to_merge']

                repo_mean = repo_pr_avg_merge_time.get(repo)
                repo_std = repo_pr_stdev_merge_time.get(repo)

                if repo_mean and repo_std and repo_std != 0:
                    df.at[index, 'time_to_merge_normalized'] = (time_to_merge - repo_mean) / repo_std

            except Exception as e:
                print(f"Error processing {row['pr_url']}: {e}")


def get_no_of_comments(repo_full_name, pr):
    return len(safe_get(pr["comments_url"], HEADERS).json()) + \
        len(safe_get(pr["review_comments_url"], HEADERS).json()) + \
        get_pr_reviews_count(repo_full_name, pr["number"], HEADERS)


def concurrent_get_normalized_no_of_comments(df, unique_repos, cache_file):
    """Fetch and normalize the number of comments for merged pull requests in all repositories."""

    def get_repo_pr_comments(repo_full_name):
        """Fetch the number of comments on all merged PRs for a given repository."""
        url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=closed&per_page=100"
        pr_comments = []

        while url:
            response = safe_get(url, HEADERS)
            if not response:
                return None

            prs = response.json()
            for pr in prs:
                if pr.get("merged_at"):
                    # 'review_comments_url' and 'comments_url'
                    num_comments = get_no_of_comments(repo_full_name, pr)
                    pr_comments.append(num_comments)

            # Pagination
            next_link = None
            if 'link' in response.headers:
                links = response.headers['link'].split(',')
                for link in links:
                    if 'rel="next"' in link:
                        next_link = link[link.find('<') + 1: link.find('>')]
                        break
            url = next_link

        return pr_comments

    def fetch_comment_stats(repo_full_name):
        """Fetch comment statistics for merged PRs in a given repository."""
        try:
            comments = get_repo_pr_comments(repo_full_name)
            if comments and len(comments) > 1:
                comment_mean = float(np.mean(comments))
                comment_std = float(np.std(comments))
                print(f"Fetched {repo_full_name}: merged_prs={len(comments)}, mean_comments={comment_mean}, std_comments={comment_std}")

                return repo_full_name, comment_mean, comment_std
        except Exception as e:
            print(f"Failed for {repo_full_name}: {e}")
        return repo_full_name, None, None

    repo_comment_mean = {}
    repo_comment_std = {}

    # Load cache if exists
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)

        for repo in unique_repos:
            if repo in cache:
                repo_comment_mean[repo] = cache[repo]['mean']
                repo_comment_std[repo] = cache[repo]['std']
    else:
        cache = {}

    to_fetch = [repo for repo in unique_repos if repo not in cache]

    if len(to_fetch) > 0:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(fetch_comment_stats, to_fetch))

        for repo, mean, std in results:
            if mean is not None:
                repo_comment_mean[repo] = mean
                repo_comment_std[repo] = std
                cache[repo] = {'mean': mean, 'std': std}

        # Save updated cache
        with open(cache_file, 'w') as f:
            json.dump(cache, f)

        for index, row in df.iterrows():
            try:
                repo = row['repository']
                comments = row['no_of_comments']

                mean = repo_comment_mean.get(repo)
                std = repo_comment_std.get(repo)

                if mean and std and std != 0:
                    df.at[index, 'no_of_comments_normalized'] = (comments - mean) / std

            except Exception as e:
                print(f"Error processing {row['pr_url']}: {e}")


def main():
    df = pd.read_csv(INPUT_CSV)

    unique_repos = df['repository'].unique()

    # concurrent_get_normalized_time_to_merge(df, unique_repos, cache_file='merge_times_cache.json')
    concurrent_get_normalized_no_of_comments(df, unique_repos, cache_file='comments_cache.json')

    df.to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    main()
