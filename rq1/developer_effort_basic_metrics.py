import os
import time
import pandas as pd
import requests
from datetime import datetime

from tqdm import tqdm

# In the run configuration, you need to set the GITHUB_TOKEN environment variable to your GitHub Personal Access Token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INPUT_CSV = '../data/final_version_conflict_prs.csv'
OUTPUT_CSV = 'result_rq1_version_conflict_prs.csv'

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


def get_pr_reviews_count(repo_full_name, pr_number):
    """Fetch the number of non-empty reviews for a pull request."""

    response = safe_get(f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews", HEADERS)
    if response is None:
        return None

    reviews = response.json()
    nonempty_reviews = [review for review in reviews if review.get('body')]

    return len(nonempty_reviews)


def get_pr_invalid_comments_count(comments_url, review_comments_url):
    """Count the number of invalid comments in a pull request."""

    invalid_comments = 0

    for url in [comments_url, review_comments_url]:
        response = safe_get(url, HEADERS)
        if response is None:
            return None

        comments = response.json()
        for comment in comments:
            if (not comment.get('body') or
                    '[bot]' in comment.get('user').get('login') or
                    comment.get('body').lower().startswith('run') or
                    comment.get('body').lower().startswith('rerun')):
                invalid_comments += 1

    return invalid_comments


def get_issue_date(issue_html_url):
    """Fetch the creation date of an issue from its HTML URL."""

    if not issue_html_url.startswith("https://github.com"):
        print(f"Invalid GitHub issue URL: {issue_html_url}")
        return None

    repo_full_name = issue_html_url.split("/")[3] + "/" + issue_html_url.split("/")[4]
    issue_number = issue_html_url.split("/")[-1]

    response = safe_get(f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}", HEADERS)
    if response is None:
        return None

    return response.json().get('created_at')


def count_java_code_changes(repo_full_name, pr_number, diff_url):
    """ Count the number of added and removed lines in Java files from a diff url."""

    response = safe_get(diff_url, HEADERS)
    if response is None:
        return None

    diff_body = response.text.splitlines()

    total_added = 0
    total_removed = 0
    count_this_file = False

    for line in diff_body:
        # Detect file changes
        if line.startswith('diff --git'):
            parts = line.strip().split(' ')
            if len(parts) >= 3:
                current_file = parts[2][2:]  # Remove the 'a/' prefix
                count_this_file = current_file.endswith('.java')
        elif count_this_file:
            # Count added or removed lines (not context or diff metadata)
            if line.startswith('+') and not line.startswith('+++'):
                total_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                total_removed += 1

    return total_added + total_removed


def main():
    df = pd.read_csv(INPUT_CSV)

    less_than_5_lines = 0
    for index, row in tqdm(df.iterrows(), total=len(df)):
        pr_url = row['pr_url']
        pr_number = pr_url.split("/")[-1]
        repo_full_name = row['repository']

        try:
            response = safe_get(f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}", HEADERS)
            if response:
                pr_data = response.json()

                # <------ Calculate total changes ------>
                if pr_data['additions'] + pr_data['deletions'] <= 5:
                    less_than_5_lines += 1

                # <------ Calculate java code changes ------>
                if pr_data['diff_url']:
                    total_java_code_changes = count_java_code_changes(repo_full_name, pr_number, pr_data['diff_url'])
                    if total_java_code_changes is not None:
                        df.at[index, 'java_code_changes'] = total_java_code_changes
                else:
                    print(f"No diff URL for PR {pr_number} in {repo_full_name}")

                # <------ Calculate comments count ------>
                total_comments = pr_data['comments'] + pr_data['review_comments']
                reviews = get_pr_reviews_count(repo_full_name, pr_number)
                df.at[index, 'comments'] = total_comments + reviews
                df.at[index, 'pure_comments'] = total_comments + reviews - get_pr_invalid_comments_count(
                    pr_data['comments_url'], pr_data['review_comments_url'])

                # <------ Calculate time to merge and detection to resolution ------>
                resolved_at = pr_data.get('merged_at')

                if resolved_at:
                    df.at[index, 'resolved_at'] = resolved_at

                    resolved_at_dt = datetime.strptime(resolved_at, "%Y-%m-%dT%H:%M:%SZ")
                    created_at = datetime.strptime(pr_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                    df.at[index, 'time_to_merge'] = (resolved_at_dt - created_at).total_seconds() / 3600  # in hours

                    detected_at = pd.NA
                    if pd.notna(row['linked_issue']):
                        # Detected_at is the date of the linked issue
                        detected_at = get_issue_date(row['linked_issue'])
                        df.at[index, 'detected_at'] = detected_at
                    elif pd.notna(row['detected_at']):
                        # Detected_at was added manually
                        detected_at = row['detected_at']

                    if pd.notna(detected_at):
                        detected_at_dt = datetime.strptime(detected_at, "%Y-%m-%dT%H:%M:%SZ")
                        df.at[index, 'time_from_detection_to_resolution'] = (resolved_at_dt - detected_at_dt).total_seconds() / 3600  # in hours

        except Exception as e:
            print(f"Error processing {pr_url}: {e}")

    df.to_csv(OUTPUT_CSV, index=False)
    print(f'{less_than_5_lines} PRs ({less_than_5_lines / len(df) * 100:.2f}%) have at most 5 lines of changes')


if __name__ == "__main__":
    main()