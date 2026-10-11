"""Pre-push hook: block tag pushes when version placeholders remain.

pre-commit passes the remote name and URL as positional arguments and
the list of refs being pushed on stdin, one per line:

    <local_ref> <local_sha> <remote_ref> <remote_sha>

This script only checks for the placeholder when a tag ref
(refs/tags/...) is being pushed — normal branch pushes pass through.
"""

import sys
from pathlib import Path

PLACEHOLDER = "__AIF_VERSION__"
REPO_ROOT = Path(__file__).resolve().parent.parent
DICT_FILES = [
    REPO_ROOT / "aif_dictionary.json",
    REPO_ROOT / "aif_dictionary.dic",
    REPO_ROOT / "aif_dictionary.yaml",
]


def main() -> int:
    pushing_tag = False
    for line in sys.stdin:
        parts = line.strip().split()
        if len(parts) >= 1 and parts[0].startswith("refs/tags/"):
            pushing_tag = True
            break

    if not pushing_tag:
        return 0

    bad_files = []
    for path in DICT_FILES:
        if path.exists() and PLACEHOLDER in path.read_text(encoding="utf-8"):
            bad_files.append(path.name)

    if bad_files:
        print(
            f"ERROR: Cannot push tag — {PLACEHOLDER} placeholder "
            f"still present in: {', '.join(bad_files)}",
            file=sys.stderr,
        )
        print(
            "Run:   python dev/update_version.py --version <version>",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
