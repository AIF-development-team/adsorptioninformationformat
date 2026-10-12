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
- The [Git Flow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) for feature work, with PR-based releases (see [Release process](#release-process))
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
  Feature branches and `develop` must never contain a stamped version; CI enforces this.
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
| [check_aif_format.py](check_aif_format.py) | Validates version consistency across all three dictionary formats. Pass `--release-tag vX.Y.Z` for strict release mode: every artifact (dictionaries, `example.aif`, `examples/**/*.aif`) must carry exactly `X.Y.Z` and no `__AIF_VERSION__` may remain. Pass `--expect-placeholder` for the opposite check used on `develop`/`feature/**`: every artifact must still hold `__AIF_VERSION__`. |
| [sync_dictionaries.py](sync_dictionaries.py) | Regenerates `aif_dictionary.yaml` and `aif_dictionary.dic` from the JSON schema. Pass `--check` to verify they are in sync without modifying files. |
| [update_version.py](update_version.py) | Stamps the version in all dictionary files, `example.aif`, and any `.aif` files under `examples/`. Auto-detects the version from the current `release/*` branch name, or accepts `--version <ver>` explicitly. |
| [check_placeholder_on_tag_push.py](check_placeholder_on_tag_push.py) | Pre-push hook that blocks tag pushes when `__AIF_VERSION__` placeholders are still present. |

## Automated checks

### CI (GitHub Actions)

Two workflows run automatically:

- **`.github/workflows/validate.yml`** — on every push to `develop`, `master`,
  `feature/**`, `release/**` and `hotfix/**`, and on PRs targeting `develop`,
  `master`, `release/**` or `hotfix/**`. Validates JSON syntax,
  version consistency (`check_aif_format.py`), and dictionary sync
  (`sync_dictionaries.py --check`), then runs the tracked test suite under
  `dev/tests/` with pytest. On `develop` and `feature/**` (pushes, and PRs
  targeting `develop`) it also runs `check_aif_format.py --expect-placeholder`,
  so a stamped version cannot reach those branches. It is also a reusable
  workflow: when called with a
  `release-tag` input it additionally runs the strict release check.
- **`.github/workflows/main.yml`** — on `vX.Y.Z` tag pushes. A `validate` job
  calls `validate.yml` with the tag (so the tagged commit gets the full test
  suite and the strict check, rejecting leftover placeholders). Only if it
  passes does the `new_release` job (the only one with `contents: write`)
  verify the version bump, generate a changelog, and create the GitHub release.
  Tags with a SemVer prerelease suffix (e.g. `v1.0.0-beta`, `v1.0.0-rc.1`) are
  published as GitHub *pre-releases*; they sort below the matching `vX.Y.Z`.

### Local hooks (pre-commit)

Install [pre-commit](https://pre-commit.com/) and activate the hooks:

```bash
pip install pre-commit
pre-commit install -c dev/.pre-commit-config.yaml
pre-commit install -c dev/.pre-commit-config.yaml --hook-type pre-push
```

The following hooks are configured in [.pre-commit-config.yaml](.pre-commit-config.yaml)
(pass `-c dev/.pre-commit-config.yaml` to other `pre-commit` commands, e.g. `run`):

| Hook | Trigger | What it does |
|---|---|---|
| `check-json` | commit | Validates `aif_dictionary.json` syntax |
| `check-yaml` | commit | Validates `aif_dictionary.yaml` syntax |
| `check-aif-version` | commit | Runs `check_aif_format.py` for cross-file version consistency |
| `sync-dictionaries` | commit | Runs `sync_dictionaries.py --check` to verify YAML/DIC match the JSON schema |
| `check-no-placeholder-on-tag` | push | Blocks tag pushes if `__AIF_VERSION__` placeholders remain |

## Release process

A release branch exists only to carry the version stamp. It is cut from
`develop`, stamped, merged into `master` by pull request, and **never merged
back into `develop`**, so `develop` keeps the placeholder. As a consequence:

- **No fixes on a release branch.** Fix on `develop` first, then cut the release.
- Use the full tag name, with the leading `v` (e.g. `v1.0.0` or
  `v1.0.0-beta`), as `<tag>`. The release branch is `release/<tag>`; the
  version stamped into the files is the tag without the `v`.

Pushing to `master` should require a pull request and the `validate` status check.

1. **Cut the release branch** from an up-to-date `develop`:

   ```bash
   git checkout develop && git pull
   git checkout -b release/<tag>
   ```

2. **Record `master` as an ancestor** (skip for the very first release). Run this
   while on `release/<tag>`. The command marks `master` as merged
   but keeps every file of `release/<tag>` unchanged (`master`'s old stamp is
   discarded):

   ```bash
   git merge -s release/<tag> origin/master -m "Sync master into release/<tag>"
   ```

3. **Regenerate derived files if the schema changed**, then **stamp** with
   [update_version.py](update_version.py) and check the result:

   ```bash
   python dev/sync_dictionaries.py
   python dev/update_version.py --version <tag>
   python dev/check_aif_format.py --release-tag <tag>
   git commit -am "Prepare release <tag>"
   git push -u origin release/<tag>
   ```

4. **Open a pull request** from `release/<tag>` into `master`. Wait
   for the `validate` check, then merge it. Do not open a PR into `develop`.

5. **Tag the merge commit on `master`**; pushing the tag triggers the release
   workflow:

   ```bash
   git checkout master && git pull
   git tag -a <tag> -m "Release <tag>"
   git push origin <tag>
   ```

6. **Verify** on [GitHub](https://github.com/AIF-development-team/adsorptioninformationformat)
   that the release was created (prerelease tags are published as pre-releases).

`develop` will show as "behind" `master` because of the stamp and sync commits;
this is expected. A hotfix applied on `master` must also be applied to
`develop` separately (e.g. by cherry-pick).

## Appendix: Git Flow

The [Git Flow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
is a branching strategy with two long-lived branches — `master` (production)
and `develop` (integration) — plus short-lived feature, release, and hotfix
branches.

- **Feature** branches (`feature/xyz`) are created from `develop` and merged
  back into `develop` when complete.
- **Release** branches (`release/v1.0.2`) are created from `develop`, stamped
  with a version, and merged into `master` by pull request, then tagged
  (e.g. `v1.0.2`). They are not merged back into `develop` (see
  [Release process](#release-process)); do not use `git flow release`.
- **Hotfix** branches are created from `master` for urgent fixes and merged
  back into `master`; apply the same fix to `develop` separately.

### Initialize Git Flow

```bash
git flow init
```

Use the default settings for all prompts. (Releases do not use Git Flow's
release commands, so the version tag prefix is not used.)

### Feature workflow

```bash
git flow feature start <feature-name>
# ... work and commit ...
git flow feature finish <feature-name>   # merges into develop
```

Or open a pull request from `feature/<feature-name>` into `develop`.

### Release workflow

See the [Release process](#release-process) section above.
