import subprocess
import sys
import re
from pathlib import Path

PLACEHOLDER = "__AIF_VERSION__"
REPO_ROOT = Path(__file__).parent.parent
MAIN_FILES = [
    REPO_ROOT / "example.aif",
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


def parse_version_string(ref_string):
    """Extract a version from a branch or tag string.

    Accepts values like *release/1.2.3*, *release/v1.2.3*, *v1.2.3* or
    *1.2.3*.  Returns the bare X.Y.Z portion or raises ValueError.
    """
    # strip any leading branch prefix
    if ref_string.startswith("release/"):
        ref_string = ref_string.split("/", 1)[1]
    # accept optional leading 'v'
    match = re.match(r"v?(\d+\.\d+\.\d+)$", ref_string)
    if match:
        return match.group(1)
    raise ValueError(f"Could not parse version from '{ref_string}'")


def get_release_version_from_branch():
    try:
        branch_name = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            encoding="utf-8",
        ).strip()
        try:
            return parse_version_string(branch_name)
        except ValueError:
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
    for path in MAIN_FILES:
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
                print(f"Skipping {path.relative_to(REPO_ROOT)} (no placeholder found)")
                continue
            path.write_text(text.replace(PLACEHOLDER, tag), encoding="utf-8")
            print(f"  Updated {path.relative_to(REPO_ROOT)}")


def is_newer_version(old_version, new_version):
    """Compare two version strings in the format X.Y.Z."""
    def parse_version(version):
        # Accept versions optionally prefixed with a leading 'v' (e.g. 'v1.2.3').
        # Versions may also be empty or match the placeholder.
        if not version or version == PLACEHOLDER:
            return (0, 0, 0)
        # strip a leading 'v' or 'V' so int conversion works
        version = version.lstrip("vV")
        return tuple(map(int, version.split(".")))

    print(f"Comparing old version '{old_version}' with new version '{new_version}'")
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
    # allow callers (e.g. CI) to supply an explicit version string
    import argparse

    parser = argparse.ArgumentParser(
        description="Update AIF version numbers in dictionary files."
    )
    parser.add_argument(
        "--version",
        dest="version",
        help=(
            "explicit version to use (e.g. from tag); "
            "overrides branch lookup"
        ),
    )
    parser.add_argument(
        "--previous",
        dest="previous",
        help="previous version/tag to compare against",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only validate the version bump without modifying files",
    )
    args = parser.parse_args()

    if args.previous:
        try:
            old_version = parse_version_string(args.previous)
        except ValueError as exc:
            print(
                f"Invalid previous version: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        old_version = get_old_version()

    if args.version:
        try:
            new_version = parse_version_string(args.version)
        except ValueError as exc:
            print(
                f"Invalid version argument: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        new_version = get_release_version_from_branch()

    if not is_newer_version(old_version, new_version):
        print(
            f"New version {new_version} is not greater than "
            f"old version {old_version}.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.check:
        print(f"Version bump OK: {old_version} → {new_version}")
    else:
        print(f"Updating AIF version from {old_version} to {new_version}")
        replace_version_placeholder(new_version)
