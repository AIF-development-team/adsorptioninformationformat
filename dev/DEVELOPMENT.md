# Development Workflow

The AIF format is an evolving format, with new mandatory or optional properties
that may be added over time. However, any changes to the AIF dictionary will
have wide-reaching consequences, given that the file format is designed to be
used in various databases and programs.

To identify the specific language and capabilities of each AIF file, it is
therefore imperative that AIF definitions are labelled with an unique format
version number, and that a record of how the file has evolved over time is
maintained.

Development paradigms detailed herein are designed to make this process easy by
relying on established programming protocols and processes.

The workflow for this project involves:

- Git for version control
- [Semantic versioning](https://semver.org/) for defining versions
- The [Git Flow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) as a development philosophy
- GitHub Actions for automatically generating releases

The [dictionary](../aif_dictionary.json) is structured with a version under the
keyword "_audit_aif_version". This follows semantic versioning conventions, and
is a required part of the file structure. This version is similarly found as the
git tag, as well as in the github release.

## Release process

To successfully make a new release the following steps should be followed.

- Create a release branch from `develop`:

  ```bash
  git flow release start <release-version>
  ```

- Check if both the dictionary and the examples are correctly updated

- Prepare the release by running [text](update_version.py):

  ```bash
  python update_version.py
  git commit -m "Prepare release <release-version>"
  ```

- Finish the release branch, which tags it and merges it into `master` and `develop`:
  ```bash
  git flow release finish <release-version>
  ```

- Push everything to GitHub to run the GH release workflow:
  ```bash
  git push --all
  git push --tags
  ```

- Go to [GitHub](https://github.com/AIF-development-team/adsorptioninformationformat) to check
  that the release has successfully completed.


## Git Flow

The Git Flow model is a branching strategy for Git, designed to facilitate
parallel development and collaboration. It defines a strict branching model that
includes two main branches with infinite lifetimes: `master` and `develop`. The
`master` branch contains production-ready code, while the `develop` branch
serves as an integration branch for features.

Feature (`feature/xyz`) branches are created from `develop` and are merged back
into `develop` when complete. Release (`release/1.0.2`) branches are created
from `develop` when preparing for a new production release, allowing for final
bug fixes and preparation. Once a release branch is ready, it is tagged
(`v1.0.2`) with the appropriate semantic versioning, then merged into both
`master` and `develop`.

Hotfix branches are created from `master` to address critical issues in
production and are merged back into both `master` and `develop` after the fix.

This model provides a robust framework for managing larger projects with
multiple developers, ensuring a clean and organized workflow.

![Git Flow Diagram](https://wac-cdn.atlassian.com/dam/jcr:cc0b526e-adb7-4d45-874e-9bcea9898b4a/04%20Hotfix%20branches.svg?cdnVersion=2493)

### 1. Initialize Git Flow

Initialize Git Flow in your repository if you haven't already:

```
git flow init
```

Select the following settings:

```
Branch name for production releases: [master]               // Enter - (default)
Branch name for "next release" development: [develop]       // Enter - (default)
Feature branches? [feature/]                                // Enter - (default)
Bugfix branches? [bugfix/]                                  // Enter - (default)
Release branches? [release/]                                // Enter - (default)
Hotfix branches? [hotfix/]                                  // Enter - (default)
Support branches? [support/]                                // Enter - (default)
Version tag prefix? []                                      // Use 'v' then Enter
Hooks and filters directory? [C:/Users/username/.git/hooks] // Enter - (default)
```

Git Flow should now be initialized on your PC.

### 2. Feature Branches

Feature branches should have a descriptive name that reflects the feature being
added, e.g., `feature/new-feature`. Branches are created from `develop` and
merged back into `develop` when a feature is complete.

- Create a new feature branch from `develop`:
  ```
  git flow feature start <feature-name>
  ```
- Work on your feature and commit changes:
  ```
  git add .
  git commit -m "Add new feature"
  ```
- When the feature is complete, finish the feature branch:
  ```
  git flow feature finish <feature-name>
  ```
  This will automatically merge it into `develop` and remove the feature branch.

### 3. Release Branches

A release branch is created when a new production release is being prepared. The
branch name contains the release version, e.g., `release/1.0.0`. A release
branch is created from the `develop` branch and upon completion will get tagged
and merged to both the `master` and `develop` branches. The only way to push to
`master` is through a release branch, except if a hotfix is needed.

- Create a release branch from `develop`:
  ```
  git flow release start <release-version>
  ```
- Prepare the release (update version number, changelog, etc.):
  ```
  git add .
  git commit -m "Prepare release <release-version>"
  ```
- Finish the release branch, which tags it and merges it into `master` and `develop`:
  ```
  git flow release finish <release-version>
  ```
