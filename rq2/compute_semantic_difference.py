import csv
import os

from semver import Version
import json

OUTPUT_CSV = 'semantic_differences.csv'


def semantic_difference(v1, v2):
    """Compute semantic distance: major, minor, patch delta"""
    try:
        v1_parsed = Version.parse(v1, optional_minor_and_patch=True)
        v2_parsed = Version.parse(v2, optional_minor_and_patch=True)

        if v1_parsed.major != v2_parsed.major:
            return "MAJOR"
        elif v1_parsed.minor != v2_parsed.minor:
            return "MINOR"
        elif v1_parsed.patch != v2_parsed.patch:
            return "PATCH"
        else:
            return "OTHER"

    except Exception as e:
        return {"error": str(e)}


def compute_semver_differences(input_json):
    diff_counts = {"MAJOR": 0, "MINOR": 0, "PATCH": 0, "OTHER": 0}

    with open(input_json, "r") as f:
        data = json.load(f)

        for dep, versions in data["conflicts"].items():
            try:
                chosen_version = dep.split(":")[-1]
                for conflicting_version in versions:
                    difference = semantic_difference(chosen_version, conflicting_version)
                    count = versions[conflicting_version]

                    if "error" not in difference:
                        diff_counts[difference] += count
                    else:
                        print(f"→ {dep}: {difference} - x{count} times")

            except Exception as e:
                print(f"  Error processing {dep}: {e}")

    total_semver_differences = sum(diff_counts.values())

    # Print summary
    print(f"\nSemantic difference summary for {data['pr_url']}:")
    print(f"  Total: {total_semver_differences}")
    for key in ["MAJOR", "MINOR", "PATCH", "OTHER"]:
        print(f"  {key}: {diff_counts[key]}")
    print(f"  Invalid: {data['total_conflicts'] - total_semver_differences}")

    # Write to CSV
    write_header = not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0
    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["pr_url", "num_modules", "total", "major", "minor", "patch", "other", "invalid_semver"])

        writer.writerow([
            data["pr_url"],
            data["num_modules"],
            total_semver_differences,
            diff_counts["MAJOR"],
            diff_counts["MINOR"],
            diff_counts["PATCH"],
            diff_counts["OTHER"],
            data["total_conflicts"] - total_semver_differences
        ])


if __name__ == "__main__":
    compute_semver_differences()
