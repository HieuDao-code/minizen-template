# Python project Template

This is a template repository for python projects.

To get started:

1. Create a repository on GitHub using this template.
2. Setup [commitizen](https://commitizen-tools.github.io/commitizen/tutorials/github_actions/#automatic-version-bumping) workflow for version and changelog generation
3. Setup [zensical](https://zensical.org/docs/publish-your-site/) workflow for documentation hosting
4. Setup [renovate](https://docs.renovatebot.com/getting-started/installing-onboarding/) for dependency updates (PRs wait 7 days after a release and are merged manually)
5. Setup [PyPI publishing](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi) workflow for package distribution
6. Install [gh-actions-lock](https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies) with `gh extension install github/gh-actions-lock` (the nix devshell does this for you) and run `gh actions-lock` after changing workflow `uses:` references
7. Optionally enable the [Require lockfile](https://docs.github.com/en/actions/how-tos/administer/enforce-workflow-lockfiles) policy so workflows only run with a valid `.github/workflows/actions.lock`
8. Enable [nix devshells](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-develop) for development environment setup with `nix develop`
9. Enable [pre-commit](https://pre-commit.com/) with `prek install`
10. Reset versioning for your project by running the following script:

```bash
#!/usr/bin/env bash
# Reset repository versioning to 0.0.0

# Clear changelog
echo "" > CHANGELOG.md

# Update version in pyproject.toml
sed -i 's/^version = "[^"]*"/version = "0.0.0"/' pyproject.toml

# Update version in commitizen version_files
sed -i 's/__version__ = "[^"]*"/__version__ = "0.0.0"/' src/minizen_template/__init__.py
```
