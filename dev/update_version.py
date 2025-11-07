import subprocess
import sys
import re
from pathlib import Path

AIF_JSON = Path(__file__).parent.parent / "aif_dictionary.json"


def get_old_version():
    with open(AIF_JSON, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r'"_audit_aif_version"\s*:\s*"([^"]+)"', line)
            if match:
                return match.group(1)
    print(
        "Could not find the old version in aif_dictionary.json. Defaulting to __AIF_VERSION__.",
        file=sys.stderr
    )
    return "__AIF_VERSION__"


def get_release_version_from_branch():
    try:
        branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                              encoding="utf-8").strip()
        match = re.match(r"release/v(\d+\.\d+\.\d+)", branch_name)
        if match:
            return match.group(1)
        else:
            print(
                f"Branch name '{branch_name}' does not conform to 'release/vX.Y.Z' format.",
                file=sys.stderr
            )
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("Could not get git branch name.", file=sys.stderr)
        sys.exit(1)


def replace_version_placeholder(tag):
    with open(AIF_JSON, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(AIF_JSON, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.replace("__AIF_VERSION__", tag))


def is_newer_version(old_version, new_version):

    def parse_version(version):
        return tuple(map(int, version.split(".")))

    try:
        return parse_version(new_version) > parse_version(old_version)
    except ValueError:
        print(
            f"Invalid version format: old_version='{old_version}', new_version='{new_version}'",
            file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    old_version = get_old_version()
    new_version = get_release_version_from_branch()
    if not is_newer_version(old_version, new_version):
        print(
            f"New version {new_version} is not greater than old version {old_version}.",
            file=sys.stderr
        )
        sys.exit(1)
    print(f"Updating AIF version from {old_version} to {new_version} in aif_dictionary.json")
    replace_version_placeholder(new_version)
