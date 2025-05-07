import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_CSV = 'java_repos_from_April_2015_min_50_stars_min_50_issues.csv'
OUTPUT_CSV = "dependency_convergence_check.csv"
MAX_WORKERS = 10
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN_2')
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}


def has_dependency_convergence_rule(owner_repo):
    owner, repo = owner_repo.split('/')
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/pom.xml"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            content = response.json().get('content')
            if content:
                import base64
                decoded_content = base64.b64decode(content).decode('utf-8')
                return check_dependency_convergence(decoded_content)
        elif response.status_code == 404:
            return 'NO_POM'
        else:
            print(f"Unexpected status code for {owner_repo}: {response.status_code}")
            return 'ERROR'
    except Exception as e:
        print(f"Error processing {owner_repo}: {e}")
        return 'ERROR'


def check_dependency_convergence(pom_content):
    try:
        root = ET.fromstring(pom_content)
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}  # common Maven POM namespace

        # Look for plugins
        plugins = root.findall(".//m:plugin", ns)
        for plugin in plugins:
            artifact_id = plugin.find("m:artifactId", ns)
            if artifact_id is not None and artifact_id.text == "maven-enforcer-plugin":
                rules = plugin.findall(".//m:rules/*", ns)
                for rule in rules:
                    if rule.tag.endswith("dependencyConvergence"):
                        return 'HAS_RULE'
        return 'NO_RULE'
    except ET.ParseError:
        return 'INVALID_XML'


def main():
    df = pd.read_csv(INPUT_CSV)
    repo_names = df['name']
    repo_names_chunk = repo_names.iloc[4000:]

    results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(has_dependency_convergence_rule, name): name for name in repo_names_chunk}

        for future in as_completed(futures):
            repo = futures[future]
            result = future.result()
            results[repo] = result

    summary_df = pd.DataFrame(list(results.items()), columns=["repository", "status"])
    print(summary_df["status"].value_counts())
    summary_df.to_csv(OUTPUT_CSV, mode='a', index=False, header=not os.path.exists(OUTPUT_CSV))


if __name__ == '__main__':
    main()
