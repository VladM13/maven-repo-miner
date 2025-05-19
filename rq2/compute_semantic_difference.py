from packaging import version
import json

INPUT_JSON = 'conflicts_before.json'


def semantic_distance(v1, v2):
    """Compute semantic distance: major, minor, patch delta"""
    try:
        v1_parsed = version.parse(v1)
        v2_parsed = version.parse(v2)

        if isinstance(v1_parsed, version.Version) and isinstance(v2_parsed, version.Version):
            if v1_parsed.major != v2_parsed.major:
                return "MAJOR"
            elif v1_parsed.minor != v2_parsed.minor:
                return "MINOR"
            elif v1_parsed.micro != v2_parsed.micro:
                return "PATCH"
            else:
                return "OTHER"

        else:
            return {"note": f"Non-standard version format: '{v1}' or '{v2}'"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    with open(INPUT_JSON, "r") as f:
        data = json.load(f)

        for dep, versions in data["conflicts"].items():
            print(f"\nDependency: {dep}")
            try:
                chosen_version = dep.split(":")[-1]
                for conflicting_version in versions:
                    distance = semantic_distance(chosen_version, conflicting_version)
                    print(f"  → Conflict with {conflicting_version}: {distance}")
            except Exception as e:
                print(f"  Error processing {dep}: {e}")