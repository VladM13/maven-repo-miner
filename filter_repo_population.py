import json
import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# In the run configuration, you need to set the GITHUB_TOKEN environment variable to your GitHub Personal Access Token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INPUT_CSV = 'filtered_repos.csv'
OUTPUT_CSV = 'filtered_repos.csv'
MAX_WORKERS = 10
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}


def check_repo_status(repo_name):
    """
    Returns:
        - ('OK', repo_name) if repo exists and does not redirect
        - ('REDIRECT', final_repo_name) if it redirects
        - ('NOT_FOUND', None) if 404
        - ('ERROR', None) if request fails
    """

    url = f"https://api.github.com/repos/{repo_name}"
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=False)
        if response.status_code in (301, 302):
            # Follow redirect manually
            location = response.headers.get('Location')
            if location:
                redirected_resp = requests.get(location, headers=HEADERS)
                if redirected_resp.status_code == 200:
                    redirected_name = urlparse(redirected_resp.json()['html_url']).path.strip('/')
                    return 'REDIRECT', redirected_name
                else:
                    print(f"Redirected to {location} but got status {redirected_resp.status_code} - {redirected_resp.text}")

            return 'REDIRECT', None  # Redirected, but unable to resolve final target
        elif response.status_code == 200:
            return 'OK', repo_name
        elif response.status_code == 404:
            return 'NOT_FOUND', None
        else:
            print(f"Unexpected status code {response.status_code} for {repo_name}")
            return 'UNKNOWN', None
    except Exception as e:
        print(f"Error checking {repo_name}: {e}")
        return 'ERROR', None


def main():
    df = pd.read_csv(INPUT_CSV)
    repo_names = df['name']
    repo_names_chunk = repo_names.iloc[5000:]

    status_map = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_repo_status, name): name for name in repo_names_chunk}

        for future in as_completed(futures):
            repo = futures[future]
            status, target = future.result()
            status_map[repo] = {'status': status, 'target': target}

    # Only remove:
    # - hidden repos: status NOT_FOUND
    # - duplicate repos: status REDIRECT where redirected target is in the dataset
    names_in_dataset = set(df['name'])
    to_remove = []

    for repo, info in status_map.items():
        status = info['status']
        target = info['target']
        if status == 'NOT_FOUND':
            to_remove.append(repo)
        elif status == 'REDIRECT' and target in names_in_dataset:
                to_remove.append(repo)

    to_remove = set(to_remove)
    filtered_df = df[~df['name'].isin(to_remove)]
    filtered_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Filtered dataset written to {OUTPUT_CSV} ({len(df) - len(filtered_df)} repos removed)")


if __name__ == '__main__':
    main()
