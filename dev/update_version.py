import subprocess
import sys
import re
from pathlib import Path

PLACEHOLDER = "__AIF_VERSION__"
REPO_ROOT = Path(__file__).parent.parent
AIF_FILES = [
    REPO_ROOT / "aif_dictionary.json",
    REPO_ROOT / "aif_dictionary.dic",
    REPO_ROOT / "aif_dictionary.yaml",
]


def get_old_version():
    """Extract the current version from aif_dictionary.json."""
    json_path = REPO_ROOT / "aif_dictionary.json"
    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r'"_audit_aif_version"\s*:\s*"([^"]+)"', line)
            if match:
                return match.group(1)
    print(
        "Could not find the old version in aif_dictionary.json. "
        f"Defaulting to {PLACEHOLDER}.",
        file=sys.stderr,
    )
    return PLACEHOLDER


def get_release_version_from_branch():
    try:
        branch_name = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            encoding="utf-8",
        ).strip()
        match = re.match(r"release/v(\d+\.\d+\.\d+)", branch_name)
        if match:
            return match.group(1)
        else:
            print(
                f"Branch name '{branch_name}' does not conform to "
                "'release/vX.Y.Z' format.",
                file=sys.stderr,
            )
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("Could not get git branch name.", file=sys.stderr)
        sys.exit(1)


def replace_version_placeholder(tag):
    """Replace __AIF_VERSION__ with *tag* in all dictionary files and
    any example AIF files under the examples directory.
    """
    # update the canonical dictionary files first
    for path in AIF_FILES:
        if not path.exists():
            print(f"Skipping {path.name} (not found)", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER not in text:
            print(f"Skipping {path.name} (no placeholder found)")
            continue
        path.write_text(text.replace(PLACEHOLDER, tag), encoding="utf-8")
        print(f"  Updated {path.name}")

    # now look for any .aif files in the examples tree and update them
    examples_dir = REPO_ROOT / "examples"
    if examples_dir.exists():
        for path in examples_dir.rglob("*.aif"):
            text = path.read_text(encoding="utf-8")
            if PLACEHOLDER not in text:
                print(f"Skipping {path.relative_to(REPO_ROOT)} (no placeholder)")
                continue
            path.write_text(text.replace(PLACEHOLDER, tag), encoding="utf-8")
            print(f"  Updated {path.relative_to(REPO_ROOT)}")


def is_newer_version(old_version, new_version):

    def parse_version(version):
        return tuple(map(int, version.split(".")))

    try:
        return parse_version(new_version) > parse_version(old_version)
    except ValueError:
        print(
            f"Invalid version format: old_version='{old_version}', "
            f"new_version='{new_version}'",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    old_version = get_old_version()
    new_version = get_release_version_from_branch()
    if not is_newer_version(old_version, new_version):
        print(
            f"New version {new_version} is not greater than "
            f"old version {old_version}.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Updating AIF version from {old_version} to {new_version}")
    replace_version_placeholder(new_version)
