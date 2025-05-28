import json
import os
import subprocess
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests

from rq2.compute_semantic_difference import compute_semver_differences

# In the run configuration, you need to set the GITHUB_TOKEN environment variable to your GitHub Personal Access Token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}
MAVEN_CMD = r"C:\Program Files\apache-maven-3.9.4\bin\mvn.cmd"
INPUT_CSV = 'overview_conflicts.csv'
TEMP_DIR = "temp_repo"


def clone_repo(repo_url: str, repo_dir: str):
    if not os.path.exists(repo_dir):
        print(f"Cloning repository: {repo_url}")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
    else:
        print(f"Repository already cloned at {repo_dir}")


def checkout_commit(repo_dir: str, commit_sha: str, before_commit: bool = False):
    if before_commit:
        print(f"Checking out the commit before {commit_sha}...")
        subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", f'{commit_sha}~1'], cwd=repo_dir, check=True)
    else:
        print(f"Checking out commit {commit_sha}...")
        subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", commit_sha], cwd=repo_dir, check=True)


def run_maven_dependency_tree(repo_dir: str, output_file: str):
    print("Running mvn dependency:tree...")
    with open(output_file, 'w') as f:
        result = subprocess.run(
            [MAVEN_CMD, "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree", "-Dverbose", "--fail-never"],
            cwd=repo_dir,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.returncode != 0:
            print("Maven failed. Error output:")
            print(result.stderr)
        return result.returncode == 0


def parse_conflicts_by_module_from_dependency_tree(file_path: str):
    # Structure: {module_name: {dep_key: {omitted_version: count}}}
    module_conflicts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    total_conflicts = 0
    current_module = None
    module_pattern = re.compile(r'dependency:.*?:tree.*?@ ([-\w.]+)')

    conflict_pattern = re.compile(
        r'([a-zA-Z0-9_.\-]+):([a-zA-Z0-9_.\-]+):.*?:([\w.\-]+):.*? -.*? omitted for conflict with ([\w.\-]+)'
    )

    with open(file_path, 'r') as f:
        for line in f:
            module_match = module_pattern.search(line)
            if module_match:
                current_module = module_match.group(1)
                continue

            match = conflict_pattern.search(line)
            if match and current_module:
                # test if the project is a single module project
                group_id = match.group(1)
                artifact_id = match.group(2)
                omitted_version = match.group(3)
                used_version = match.group(4)

                key = f"{group_id}:{artifact_id}:{used_version}"
                module_conflicts[current_module][key][omitted_version] += 1
                total_conflicts += 1

    affected_modules = len(module_conflicts.keys())

    return total_conflicts, affected_modules, dict(module_conflicts)


def detect_conflicting_versions(pr_url, repo_url, commit_sha, before_commit, json_output_file):
    repo_path = Path(TEMP_DIR).resolve()
    clone_repo(repo_url, str(repo_path))

    checkout_commit(str(repo_path), commit_sha, before_commit)

    output_file = "dep_tree.txt"
    total_conflicts = 0
    if run_maven_dependency_tree(str(repo_path), str(output_file)):
        total_conflicts, affected_modules, conflicts = parse_conflicts_by_module_from_dependency_tree(str(output_file))

        with open(json_output_file, "w") as f:
            json.dump({
                "pr_url": pr_url,
                "total_conflicts": total_conflicts,
                "affected_modules": affected_modules,
                "conflicts": conflicts},
                f, indent=4)

        if conflicts:
            print(f"{total_conflicts} conflicts in {affected_modules} modules saved to {json_output_file}")
        else:
            print("No conflicting versions found.")

    # Optional: clean up
    # subprocess.run(["rmdir", "/S", "/Q", repo_path], shell=True)

    return total_conflicts


def process_pr(pr_url, force=False):
    parts = pr_url.strip("/").split("/")
    owner, repo, pr_number = parts[-4], parts[-3], parts[-1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    response = requests.get(api_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch PR data: {response.status_code} - {response.text}")
        exit(1)

    pr_commit_sha = response.json().get("merge_commit_sha")
    pr_base_sha = response.json().get("base").get("sha")
    repo_url = response.json().get("base").get("repo").get("clone_url")
    json_output_file = f"cache/conflicts_before_{owner}_{repo}_{pr_number}.json"

    if not os.path.exists(json_output_file) or force:
        total_conflicts = detect_conflicting_versions(pr_url, repo_url, pr_base_sha, before_commit=False,
                                json_output_file=json_output_file)
        return total_conflicts, json_output_file
    else:
        # Use cached data
        return -1, json_output_file

    # print("--------------------------------")
    # detect_conflicting_versions(pr_url, repo_url, pr_commit_sha, before_commit=False,
    #                             json_output_file="conflicts_after.json")


# Example usage:
if __name__ == "__main__":
    # Check if the Maven command is available
    result = subprocess.run([MAVEN_CMD, "--version"], stdout=subprocess.DEVNULL, check=True)
    if result.returncode != 0:
        print("Maven command not found. Please check your Maven installation.")
        exit(1)

    df = pd.read_csv(INPUT_CSV)
    df = df.iloc[0:1]

    for index, row in df.iterrows():
        pr_url = row['pr_url']
        print(f"\n------------------------------\nProcessing PR: {pr_url}")
        total_conflicts, json_output = process_pr(pr_url, force=True)

        # if total_conflicts > 0:
        compute_semver_differences(json_output)
