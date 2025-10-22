import subprocess
import sys
from pathlib import Path

AIF_JSON = Path(__file__).parent.parent / "aif_dictionary.json"


def get_latest_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"],
                                      encoding="utf-8").strip()
        return tag
    except subprocess.CalledProcessError:
        print("Could not get git tag.", file=sys.stderr)
        sys.exit(1)


def replace_version_placeholder(tag):
    with open(AIF_JSON, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(AIF_JSON, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.replace("__AIF_VERSION__", tag))


if __name__ == "__main__":
    tag = get_latest_tag()
    replace_version_placeholder(tag)
