# Development Workflow

The AIF format is an evolving format, with new mandatory or optional properties
that may be added over time. However, any changes to the AIF dictionary will
have wide-reaching consequences, given that the file format is designed to be
used in various databases and programs.

To identify the specific language and capabilities of each AIF file, it is
therefore imperative that AIF definitions are labelled with a unique format
version number, and that a record of how the file has evolved over time is
maintained.

Development paradigms detailed herein are designed to make this process easy by
relying on established programming protocols and processes.

**Contents:**
[Version strings](#version-strings) · [Dev scripts](#dev-scripts) ·
[Automated checks](#automated-checks) · [Release process](#release-process) ·
[Git Flow](#appendix-git-flow)

The workflow for this project involves:

- Git for source control
- [Semantic versioning](https://semver.org/) for defining versions
- The [Git Flow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) as a development philosophy
- Scripts for propagating version strings when ready for release
- Local pre-commit / pre-push hooks and CI for checking file consistency
- GitHub Actions for automatically generating releases

## Version strings

The [JSON schema](../aif_dictionary.json) is the **single source of truth**.
It contains the version under the keyword `_audit_aif_version`, which follows
semantic versioning conventions and is a required part of every AIF file.
This version is also reflected in the git tag and GitHub release.

The version across branches:

- On the `master` branch, all files contain the latest released version.
- On the `develop` branch, the version is replaced by a placeholder (`__AIF_VERSION__`).
- Each tag has file version strings corresponding to its version.

The version must be consistent across **all** dictionary representations
and every example AIF file:

- `aif_dictionary.json` – JSON Schema (`version`, `$id` URL, `_audit_aif_version.const`)
- `aif_dictionary.dic`  – DDLm CIF dictionary (`_dictionary.version`, `_enumeration.default`)
- `aif_dictionary.yaml` – LinkML schema (`version`)
- `example.aif` at the repository root
- All `.aif` files under the `./examples` directory

## Dev scripts

The `dev/` directory contains helper scripts used during development and CI:

| Script | Purpose |
|---|---|
| [check_aif_format.py](check_aif_format.py) | Validates version consistency across all three dictionary formats. |
| [sync_dictionaries.py](sync_dictionaries.py) | Regenerates `aif_dictionary.yaml` and `aif_dictionary.dic` from the JSON schema. Pass `--check` to verify they are in sync without modifying files. |
| [update_version.py](update_version.py) | Stamps the version in all dictionary files, `example.aif`, and any `.aif` files under `examples/`. Auto-detects the version from the current `release/*` branch name, or accepts `--version <ver>` explicitly. |
| [check_placeholder_on_tag_push.py](check_placeholder_on_tag_push.py) | Pre-push hook that blocks tag pushes when `__AIF_VERSION__` placeholders are still present. |

## Automated checks

### CI (GitHub Actions)

Two workflows run automatically:

- **`.github/workflows/validate.yml`** — on every push and PR to `develop`,
  `master`, `feature/**`, and `release/**` branches.  Validates JSON syntax,
  version consistency (`check_aif_format.py`), and dictionary sync
   (`sync_dictionaries.py --check`), then runs the tracked test suite under
   `dev/tests/` with pytest.
- **`.github/workflows/main.yml`** — on tag pushes. Runs the same validations,
  verifies the version bump, generates a changelog, and creates a GitHub release.

### Local hooks (pre-commit)

Install [pre-commit](https://pre-commit.com/) and activate the hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

The following hooks are configured in `.pre-commit-config.yaml`:

| Hook | Trigger | What it does |
|---|---|---|
| `check-json` | commit | Validates `aif_dictionary.json` syntax |
| `check-yaml` | commit | Validates `aif_dictionary.yaml` syntax |
| `check-aif-version` | commit | Runs `check_aif_format.py` for cross-file version consistency |
| `sync-dictionaries` | commit | Runs `sync_dictionaries.py --check` to verify YAML/DIC match the JSON schema |
| `check-no-placeholder-on-tag` | push | Blocks tag pushes if `__AIF_VERSION__` placeholders remain |

## Release process

1. **Create a release branch** from `develop`:

   ```bash
   git flow release start <release-version>
   ```

2. **Verify dictionary and examples** are correctly updated. If the JSON schema
   was changed, regenerate the derived files:

   ```bash
   python dev/sync_dictionaries.py
   ```

3. **Stamp the version** by running [update_version.py](update_version.py),
   which replaces the `__AIF_VERSION__` placeholder in all three dictionary
   files, `example.aif`, and any `.aif` files under `examples/`:

   ```bash
   python dev/update_version.py
   git add -A
   git commit -m "Prepare release <release-version>"
   ```

4. **Finish the release branch** (tags and merges into `master` and `develop`):

   ```bash
   git flow release finish <release-version>
   ```

5. **Push everything** to trigger the GitHub release workflow:

   ```bash
   git push --all
   git push --tags
   ```

6. **Verify** on [GitHub](https://github.com/AIF-development-team/adsorptioninformationformat)
   that the release was created successfully.

## Appendix: Git Flow

The [Git Flow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
is a branching strategy with two long-lived branches — `master` (production)
and `develop` (integration) — plus short-lived feature, release, and hotfix
branches.

- **Feature** branches (`feature/xyz`) are created from `develop` and merged
  back into `develop` when complete.
- **Release** branches (`release/v1.0.2`) are created from `develop`, stamped
  with a version, tagged (e.g. `v1.0.2`), and merged into both `master` and
  `develop`.
- **Hotfix** branches are created from `master` for urgent fixes and merged
  back into both `master` and `develop`.

### Initialize Git Flow

```bash
git flow init
```

Use the default settings for all prompts, except set the version tag prefix
to `v`:

```
Version tag prefix? [] → v
```

### Feature workflow

```bash
git flow feature start <feature-name>
# ... work and commit ...
git flow feature finish <feature-name>   # merges into develop
```

### Release workflow

See the [Release process](#release-process) section above for the full
step-by-step procedure.
