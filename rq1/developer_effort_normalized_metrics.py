import os
import time
import json
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# In the run configuration, set the GITHUB_TOKEN environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INPUT_CSV = 'rq1_repositories_with_version_conflict_pulls.csv'
OUTPUT_CSV = 'new_rq1_repositories_with_version_conflict_pulls.csv'

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}


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


def try_load_cache(cache_file, unique_repos):
    """Load the cache from a file if it exists, otherwise create an empty cache."""

    repo_mean = {}
    repo_std = {}

    # Load cache if it exists
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)

        for repo in unique_repos:
            if repo in cache:
                repo_mean[repo] = cache[repo]['mean']
                repo_std[repo] = cache[repo]['std']
    else:
        cache = {}
    return cache, repo_mean, repo_std


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

    cache, repo_pr_avg_merge_time, repo_pr_stdev_merge_time = try_load_cache(cache_file, unique_repos)

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
            json.dump(cache, f, indent=2)

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





def concurrent_get_normalized_no_of_comments(df, unique_repos, cache_file):
    """Fetch and normalize the number of comments for merged pull requests in all repositories."""

    def get_pr_reviews_count_graphql(repo_full_name, pr_number):
        """Fetch the number of non-empty reviews for a pull request using GraphQL."""
        owner, repo = repo_full_name.split("/")
        non_empty_reviews = 0
        has_next_page = True
        after_cursor = "null"  # first page has no cursor

        def build_query(after_cursor):
            cursor_part = f', after: "{after_cursor}"' if after_cursor != "null" else ""
            return f"""
            {{
              repository(owner: "{owner}", name: "{repo}") {{
                pullRequest(number: {pr_number}) {{
                  reviews(first: 100{cursor_part}) {{
                    nodes {{
                      body
                    }}
                    pageInfo {{
                      hasNextPage
                      endCursor
                    }}
                  }}
                }}
              }}
            }}
            """

        url = "https://api.github.com/graphql"

        while has_next_page:
            query = build_query(after_cursor)
            response = requests.post(url, json={"query": query}, headers=HEADERS)

            if response.status_code != 200:
                print(f"GraphQL query failed: {response.status_code} - {response.text}")
                return None

            pr_data = response.json()["data"]["repository"]["pullRequest"]

            reviews_data = pr_data["reviews"]
            non_empty_reviews += sum(1 for r in reviews_data["nodes"] if r["body"])

            has_next_page = reviews_data["pageInfo"]["hasNextPage"]
            after_cursor = reviews_data["pageInfo"]["endCursor"]

        return non_empty_reviews

    def get_no_of_comments(repo_full_name, pr):
        """Fetch the total number of comments for a pull request."""

        pr_data = safe_get(pr['url'], HEADERS)
        if not pr_data:
            return None

        pr_data = pr_data.json()
        total_comments = pr_data['comments'] + pr_data['review_comments']
        reviews = get_pr_reviews_count_graphql(repo_full_name, pr['number'])

        return total_comments + reviews

    def get_repo_pr_comments(repo_full_name):
        """Fetch the number of comments on all merged PRs for a given repository."""

        url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=closed&per_page=100"
        pr_comments = []

        while url:
            response = safe_get(url, HEADERS)
            if not response:
                return None

            prs = response.json()
            merged_prs = [pr for pr in prs if pr.get("merged_at")]

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(get_no_of_comments, repo_full_name, pr) for pr in merged_prs]

                for future in as_completed(futures):
                    num_comments = future.result()
                    pr_comments.append(num_comments)

            print(f"Finished {len(merged_prs)} PRs: So far found {len(pr_comments)} comments for {repo_full_name}")
            if len(pr_comments) > 200:
                print(f"Found {len(pr_comments)} comments for {repo_full_name}, stopping early.")
                return np.random.choice(pr_comments, 200, replace=False)

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

    cache, repo_comment_mean, repo_comment_std = try_load_cache(cache_file, unique_repos)
    to_fetch = [repo for repo in unique_repos if repo not in cache]

    if len(to_fetch) == 0:
        return

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_comment_stats, to_fetch))

    for repo, mean, std in results:
        if mean is not None:
            repo_comment_mean[repo] = mean
            repo_comment_std[repo] = std
            cache[repo] = {'mean': mean, 'std': std}

    # Save updated cache
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

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

    df = df.iloc[:3]
    print(df)

    unique_repos = df['repository'].unique()

    # concurrent_get_normalized_time_to_merge(df, unique_repos, cache_file='merge_times_cache.json')
    concurrent_get_normalized_no_of_comments(df, unique_repos, cache_file='comments_cache.json')

    df.to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    main()
