import os
import pandas as pd
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

INPUT_CSV = 'java_repos_from_April_2015_min_50_stars_min_50_issues.csv'
MAX_WORKERS = 10
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}


def get_redirect_url(repo_name):
    url = f"https://api.github.com/repos/{repo_name}"
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=False)
        if response.status_code in (301, 302) and 'Location' in response.headers:
            new_location = response.headers['Location']
            response = requests.get(new_location, headers=HEADERS, allow_redirects=False)
            new_url = response.json().get('html_url')
            return urlparse(new_url).path.strip('/')

        elif response.status_code == 404:
            return "NOT_FOUND"
        else:
            return None  # No redirect
    except Exception as e:
        print(f"Error fetching {repo_name}: {e}")
        return None


def main():
    df = pd.read_csv(INPUT_CSV)
    repo_names = df['name']
    repo_names_chunk = repo_names.iloc[:1000]

    redirect_map = defaultdict(list)  # Maps final target to list of repos that redirect there

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(get_redirect_url, name): name for name in repo_names_chunk}

        for future in as_completed(futures):
            original_repo_name = futures[future]
            redirect_repo_name = future.result()
            if redirect_repo_name and redirect_repo_name != "NOT_FOUND":
                redirect_map[redirect_repo_name].append(original_repo_name)

    print("Repositories redirected to the same URL:")
    for target_url, repos in redirect_map.items():
        print(f"\nTarget: {target_url}")
        if target_url not in repo_names.values:
            print("  - Not in the dataset")
        for repo in repos:
            print(f"  - {repo}")


if __name__ == '__main__':
    main()
