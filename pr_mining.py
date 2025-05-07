import datetime

import pandas as pd
import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

INPUT_CSV = 'java_repos_from_April_2015_min_50_stars_min_50_issues.csv'
OUTPUT_CSV = 'repositories_with_version_conflict_pulls.csv'
RATE_LIMIT_SLEEP = 10  # seconds
MAX_WORKERS = 10      # number of parallel threads

KEYWORDS = ['version conflict', 'library conflict', 'nosuchmethoderror']


def discusses_version_conflict(issue):
    """Check if an issue discusses version conflicts based on keywords."""
    title = issue.get('title', '').lower()
    body = issue.get('body', '').lower() if issue.get('body') else ''
    for keyword in KEYWORDS:
        if keyword in title or keyword in body:
            return True
    return False


def pr_modifies_pom(repo_full_name, pr_number):
    """Check if a pull request modifies a pom.xml file."""
    url = f'https://patch-diff.githubusercontent.com/raw/{repo_full_name}/pull/{pr_number}.diff'
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 403 or response.status_code == 429:
        print(f"Rate limit reached ({response.status_code}) during PR diff check for {repo_full_name} PR#{pr_number}, retrying after {RATE_LIMIT_SLEEP}s...")
        time.sleep(RATE_LIMIT_SLEEP)
        return pr_modifies_pom(repo_full_name, pr_number)

    if response.status_code != 200:
        print(f"Failed to fetch PR diff for {repo_full_name} PR#{pr_number}: {response.status_code} - {response.text}")
        return False

    return "pom.xml" in response.text


def search_issues_for_repo(repo_full_name):
    """Search all issues for a given repository and collect matches."""
    matches = []
    url = f'https://api.github.com/repos/{repo_full_name}/issues'
    params = {
        'state': 'all',
        'per_page': 100
    }

    while url:  # Keep making requests as long as the URL is not empty (i.e., there's more data)
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 403:
            print(f"Rate limit reached ({response.status_code}) while fetching issues for {repo_full_name}, retrying after {RATE_LIMIT_SLEEP}s...")
            time.sleep(RATE_LIMIT_SLEEP)
            continue

        if response.status_code != 200:
            print(f"Failed to fetch issues for {repo_full_name}: {response.status_code} - {response.text}")
            break

        issues = response.json()

        # Process the issues
        for issue in issues:
            if 'pull_request' in issue and discusses_version_conflict(issue):
                pr_number = issue.get('number')
                pr_merged_date = issue.get('pull_request').get('merged_at')

                if (pr_merged_date is None or
                        '[bot]' in issue.get('user').get('login') or
                        not pr_modifies_pom(repo_full_name, pr_number)):
                    # Ignore PRs that are not merged, created by dependabot or do not modify the pom.xml
                    continue

                matches.append({
                    'repository': repo_full_name,
                    'pr_title': issue.get('title'),
                    'pr_url': issue.get('html_url')
                })
                print(f"Found match: {repo_full_name} - {issue.get('html_url')}")

        # Check if there's another page
        # https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28
        if 'link' in response.headers:
            link_header = response.headers['link']

            # Look for the 'next' link (pagination)
            next_page_url = None
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    next_page_url = link[link.find('<')+1:link.find('>')]
                    break

            # Update the URL for the next request
            url = next_page_url
        else:
            url = None  # No more pages

    return matches


def main():
    #### Check rate limit ####
    response = requests.get('https://api.github.com/rate_limit', headers=HEADERS)
    if response.status_code == 200:
        print(response.text)
        print(datetime.datetime.fromtimestamp(response.json().get('resources').get('core').get('reset')))
        print(datetime.datetime.fromtimestamp(response.json().get('resources').get('graphql').get('reset')))

    return
    ##########################

    df = pd.read_csv(INPUT_CSV)


    START_INDEX = 6200
    END_INDEX = 6200
    df_chunk = df.iloc[START_INDEX:END_INDEX]

    all_matches = deque()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(search_issues_for_repo, row['name']): row['name']
            for _, row in df_chunk.iterrows()
        }

        for future in as_completed(futures):
            repo_name = futures[future]
            try:
                matches = future.result()
                all_matches.extend(matches) # thread-safe
            except Exception as e:
                print(f"Error processing repo {repo_name}: {e}")

    if all_matches:
        results_df = pd.DataFrame(all_matches)

        # Append to the CSV output file
        results_df.to_csv(OUTPUT_CSV, mode='a', index=False, header=not os.path.exists(OUTPUT_CSV))

        print(f"✅ Done! Saved results to {OUTPUT_CSV}")
    else:
        print("❌ No matching issues found.")


if __name__ == "__main__":
    main()