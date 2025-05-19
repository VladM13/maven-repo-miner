import json
import os
import subprocess
import re
import shutil
from collections import defaultdict
from pathlib import Path

REPO_URL = "https://github.com/stargate/stargate.git"
PR_COMMIT_SHA = "5c3695f"

MAVEN_CMD = r"C:\Program Files\apache-maven-3.9.4\bin\mvn.cmd"
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
        subprocess.run(["git", "checkout", f'{commit_sha}~1'], cwd=repo_dir, check=True)
    else:
        print(f"Checking out commit {commit_sha}...")
        subprocess.run(["git", "checkout", commit_sha], cwd=repo_dir, check=True)


def run_maven_dependency_tree(repo_dir: str, output_file: str):
    print("Running mvn dependency:tree...")
    result = subprocess.run(
        [MAVEN_CMD, "dependency:tree", "-Dverbose", f"-DoutputFile={output_file}"],
        cwd=repo_dir,
        stdout=subprocess.DEVNULL,
        text=True
    )

    if result.returncode != 0:
        print("Maven failed. Error output:")
        print(result.stderr)
    return result.returncode == 0


def parse_conflicts_from_dependency_tree(file_path: str):
    # Structure: {"groupId:artifactId:used_version": {"omitted_version": count, ...}, ...}
    conflict_summary = defaultdict(lambda: defaultdict(int))
    total_conflicts = 0

    pattern = re.compile(
        r'([a-zA-Z0-9_.\-]+):([a-zA-Z0-9_.\-]+):.*?:([\w.\-]+):.*? - omitted for conflict with ([\w.\-]+)'
    )

    with open(file_path, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                group_id = match.group(1)
                artifact_id = match.group(2)
                omitted_version = match.group(3)
                used_version = match.group(4)

                key = f"{group_id}:{artifact_id}:{used_version}"
                conflict_summary[key][omitted_version] += 1
                total_conflicts += 1

    return total_conflicts, conflict_summary


def detect_conflicting_versions(repo_url, commit_sha, before_commit, json_output_file):
    repo_path = Path(TEMP_DIR).resolve()
    clone_repo(repo_url, str(repo_path))

    checkout_commit(str(repo_path), commit_sha, before_commit)

    output_file = repo_path / "dep_tree.txt"
    if run_maven_dependency_tree(str(repo_path), str(output_file)):
        total_conflicts, conflicts = parse_conflicts_from_dependency_tree(str(output_file))

        if conflicts:
            with open(json_output_file, "w") as f:
                json.dump({"total_conflicts": total_conflicts, "conflicts": conflicts}, f, indent=4)

            print(f"{total_conflicts} conflicts saved to {json_output_file}")
        else:
            print("No conflicting versions found.")

    # # Optional: clean up
    # shutil.rmtree(repo_path)


# Example usage:
if __name__ == "__main__":
    # Check if the Maven command is available
    result = subprocess.run([MAVEN_CMD, "--version"], stdout=subprocess.DEVNULL, check=True)
    if result.returncode != 0:
        print("Maven command not found. Please check your Maven installation.")
        exit(1)

    detect_conflicting_versions(REPO_URL, PR_COMMIT_SHA, before_commit=True, json_output_file="conflicts_before.json")

    print("--------------------------------")

    detect_conflicting_versions(REPO_URL, PR_COMMIT_SHA, before_commit=False, json_output_file="conflicts_after.json")

