import csv
import os

from semver import Version
import json

OUTPUT_CSV = 'semantic_differences.csv'
OUTPUT_JSON = 'semantic_differences_per_module.json'


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


def parse_diff_counts_from_json(input_json):
    diff_counts = {"MAJOR": 0, "MINOR": 0, "PATCH": 0, "OTHER": 0, "INVALID": 0}

    # Structure: {module_name: {MAJOR: <int>, MINOR: <int>, PATCH: <int>, OTHER: <int>, INVALID: <int>}}
    diff_counts_per_module = {}

    with open(input_json, "r") as f:
        data = json.load(f)

        for module in data["conflicts"]:
            if module not in diff_counts_per_module:
                diff_counts_per_module[module] = {"MAJOR": 0, "MINOR": 0, "PATCH": 0, "OTHER": 0, "INVALID": 0}
            else:
                # modules should be unique
                raise ValueError(f"Module {module} already exists in diff_counts")

            for dep, versions in data['conflicts'][module].items():
                try:
                    chosen_version = dep.split(":")[-1]
                    for conflicting_version in versions:
                        difference = semantic_difference(chosen_version, conflicting_version)
                        count = versions[conflicting_version]

                        if "error" not in difference:
                            diff_counts[difference] += count
                            diff_counts_per_module[module][difference] += count
                        else:
                            print(f"→ {dep}: {difference} - x{count} times")
                            diff_counts['INVALID'] += count
                            diff_counts_per_module[module]['INVALID'] += count

                except Exception as e:
                    print(f"  Error processing module {module} - {dep}: {e}")

    return data, diff_counts, diff_counts_per_module


def print_and_write_summary_to_csv(data, diff_counts):
    total_conflicts = sum(diff_counts.values())

    # Print a summary of all semantic differences
    print(f"\nSemantic difference summary for {data['pr_url']}:")
    print(f"  Total: {total_conflicts}")
    for key in ["MAJOR", "MINOR", "PATCH", "OTHER", "INVALID"]:
        print(f"  {key}: {diff_counts[key]}")

    # Write summary to CSV
    write_header = not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0
    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(
                ["pr_url", "affected_modules", "total", "major", "minor", "patch", "other", "invalid_semver"])

        writer.writerow([
            data["pr_url"],
            data["affected_modules"],
            total_conflicts,
            diff_counts["MAJOR"],
            diff_counts["MINOR"],
            diff_counts["PATCH"],
            diff_counts["OTHER"],
            diff_counts["INVALID"]
        ])


def print_and_write_per_module_to_json(data, diff_counts_per_module):
    # Load existing output
    if os.path.exists(OUTPUT_JSON) and os.stat(OUTPUT_JSON).st_size > 0:
        with open(OUTPUT_JSON, "r") as f:
            output_data = json.load(f)
    else:
        output_data = {}

    # Build per-module output under the PR URL
    pr_data = {}
    for module, diff_counts in diff_counts_per_module.items():
        total_conflicts_in_module = sum(diff_counts.values())

        pr_data[module] = {
            "MAJOR": diff_counts["MAJOR"],
            "MINOR": diff_counts["MINOR"],
            "PATCH": diff_counts["PATCH"],
            "OTHER": diff_counts["OTHER"],
            "INVALID_SEMVER": diff_counts["INVALID"],
            "TOTAL": total_conflicts_in_module
        }
    # Structure:
    # {pr_url:
    #   [
    #       {
    #           module_name: {MAJOR: <int>, MINOR: <int>, PATCH: <int>, OTHER: <int>, INVALID_SEMVER: <int>, TOTAL: <int>}
    #       }
    #   ]
    # }
    output_data[data['pr_url']] = pr_data

    # Write updated result back
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output_data, f, indent=2)


def compute_semver_differences(input_json):
    data, diff_counts, diff_counts_per_module = parse_diff_counts_from_json(input_json)

    print_and_write_summary_to_csv(data, diff_counts)
    print_and_write_per_module_to_json(data, diff_counts_per_module)
