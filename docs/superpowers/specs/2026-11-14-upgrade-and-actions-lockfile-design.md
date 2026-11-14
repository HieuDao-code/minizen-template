# Upgrade tooling and adopt GitHub Actions lockfile

## Intent

Improve supply-chain security of the template. Bring every pinned tool and
package up to date, and lock GitHub Actions dependencies with
`.github/workflows/actions.lock` (GA since 2026-10-28), following the approach in
Hugo van Kemenade's "Lock your GitHub Actions" (2026-11-11).

## Goals

- All versions current, respecting the existing 7-day cooldown:
  - Python dependency groups in `pyproject.toml` (exact `==` pins)
  - `uv.lock`
  - `uv_build` bound
  - prek hooks in `prek.toml` and `minimum_prek_version`
  - uv version in workflows
  - nix flake
- zizmor at >= v1.32.0 (first version that understands lockfiles), and the same
  version in `pyproject.toml` and `prek.toml`.
- Workflows use readable tag refs (`actions/checkout@v7.x.y`); commit SHAs,
  owner IDs and repo IDs live in `actions.lock`.
- CI fails on PRs when the lockfile is stale or a locked pin no longer verifies.
- Renovate keeps both workflows and lockfile updated; its PRs reach a green
  state but are merged manually.

## Non-goals

- Switching to Dependabot.
- CODEOWNERS for the lockfile (single-maintainer template).
- Turning on the "Require lockfile" policy (a GitHub setting, not repo content;
  documented as a setup step in the README instead).

## Anti-goals

- Renovate re-pinning actions to SHAs, fighting the lockfile.
- A lockfile that can silently drift from the workflows.

## Approaches considered

- **Keep Renovate (chosen).** Renovate regenerates `actions.lock` when it bumps
  an action (experimental, uses `--relock`). It already covers uv, prek hooks
  and nix with a monthly schedule and a 7-day minimum release age.
- **Switch to Dependabot.** First-party lockfile support, but it only reads
  `.pre-commit-config.yaml` (not `prek.toml`), its nix support excludes private
  repos, and grouping, schedule and cooldown would need rebuilding.
- **Hybrid.** Rejected: two bots on one repo.

## Design

1. **Upgrade.** Bump the pins in `pyproject.toml`, then run `uv lock --upgrade`,
   `prek update --freeze` and `nix flake update`. Set the workflow `uv` version to
   the latest release that is at least 7 days old.
2. **Lockfile.** Rewrite the `uses:` refs in all five workflows from SHA plus
   comment to full version tags. Run `gh actions-lock` and commit
   `.github/workflows/actions.lock` alongside the workflows.
3. **Verify in CI.** Add `.github/workflows/lockfile.yml`, triggered on
   `pull_request` to `main`. It has `permissions: {}` and runs on `ubuntu-slim`
   with `GH_TOKEN: ${{ github.token }}`. It checks out the repo with
   `persist-credentials: false`, then runs
   `gh extension install github/gh-actions-lock --pin vX.Y.Z` and
   `gh actions-lock --verify`. The lockfile includes this workflow.
4. **Renovate.**
   - Add `ignorePresets: ["helpers:pinGitHubActionDigests"]` so
     `config:best-practices` stops pinning action digests.
   - Add a regex `customManagers` entry so Renovate bumps the `--pin` version of
     gh-actions-lock in `lockfile.yml`. It uses the `github-releases` datasource
     for `github/gh-actions-lock`.
5. **Dev tooling.**
   - Replace `pinact` with `gh` in `flake.nix`, and install the gh-actions-lock
     extension in the `shellHook` if it is missing.
   - In `justfile` `update`, replace `pinact run ...` with
     `gh actions-lock` (no `--relock`, which would accept upstream-moved tags). Action version bumps come from Renovate.
6. **Docs.** Update the README setup steps: install gh-actions-lock, and
   optionally enable the "Require lockfile" policy.
7. **Unstick Renovate PRs, keeping a 7-day cooldown everywhere, with no
   automerge.**
   - Problem: the monthly lock-maintenance PR (#15) stays "UNSTABLE" because
     `renovate/stability-days` never resolves. Lock refreshes have no release
     timestamp for Renovate to age. CI (Test, zizmor) passes.
   - `uv.lock`: keep Renovate `lockFileMaintenance`, scoped to uv only. Set its
     `minimumReleaseAge` to `null`; the cooldown is enforced by uv's
     `exclude-newer = "1 week"`, which `uv lock --upgrade` honours.
   - `flake.lock`: remove it from Renovate (disable the nix manager). In
     `just update`, lock nixpkgs to the newest `nixpkgs-unstable` commit that is
     at least 7 days old: look it up via the GitHub API, then run
     `nix flake lock --override-input nixpkgs github:NixOS/nixpkgs/<sha>`.
   - Normal version-bump PRs keep `minimumReleaseAge: "7 days"`.
   - No automerge: drop `schedule:automergeMonthly` and keep a monthly schedule.
     Merging stays manual.

## Left to the builder

- Exact versions chosen (latest that is at least 7 days old).
- Whether new zizmor findings appear after the upgrade, and fixing them.
