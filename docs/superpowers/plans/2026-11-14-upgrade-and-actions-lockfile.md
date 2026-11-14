# Tool Upgrades and Actions Lockfile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update every pinned tool and package, lock GitHub Actions with
`actions.lock`, and get Renovate PRs out of the stuck-pending state. Keep a
7-day cooldown everywhere and no automerge.

**Architecture:** The work is config only. Pins live in `pyproject.toml`,
`prek.toml`, workflow YAML and `flake.lock`. The actions lockfile is generated
by the `gh actions-lock` extension and verified in CI. Cooldowns are enforced by
the tool that writes each lockfile:

- uv: `exclude-newer`
- prek: `cooldown_days`
- nixpkgs: a 7-day-old commit picked in `just update`
- Renovate: `minimumReleaseAge` for normal updates

**Tech Stack:** uv, prek, zizmor, GitHub Actions, gh-actions-lock, Renovate,
nix flakes, just.

**Spec:** `docs/superpowers/specs/2026-11-14-upgrade-and-actions-lockfile-design.md`

## Global Constraints

- Cooldown: every chosen version must have been released on or before
  **2026-11-07**, which is 7 days before 2026-11-14.
- zizmor `1.32.0` or later. Use the same version in `pyproject.toml` and
  `prek.toml`.
- gh-actions-lock pinned at `v0.4.1`.
- uv in CI: `0.13.7`. 0.13.8 is too new.
- `uv_build` bound must admit the uv version in use:
  `uv_build>=0.13.7,<0.14`.
- Renovate: no automerge anywhere, a monthly schedule, and
  `minimumReleaseAge: "7 days"` for normal updates.
- Workflow `uses:` refs are full version tags such as `@v7.0.1`, never SHAs or
  partial tags such as `@v7`.
- Keep `permissions: {}` at the workflow level and `persist-credentials: false`
  on every checkout.

## Review Focus

1. **Renovate re-pins SHAs.** `config:best-practices` pulls in
   `helpers:pinGitHubActionDigests`. Task 3 checks that the resolved config
   ignores it.
2. **A new workflow is missing from the lockfile.** `lockfile.yml` must itself
   be in `actions.lock`. Task 2 runs `--verify` after adding it.
3. **zizmor flags tag refs.** A zizmor older than 1.32 complains about
   unpinned `uses`. Task 2 runs zizmor locally with the bumped version.
4. **The nixpkgs pick is newer than 7 days.** For example, the GitHub API
   `until` filter could be mis-formatted. Task 4 checks `lastModified` in
   `flake.lock`.
5. **uv in CI can't read the lock written by a newer local uv.** CI uv is
   0.13.7, so Task 1 locks with uv 0.13.7 via `uvx uv@0.13.7`, or checks that
   CI's `uv sync --locked` passes.

---

### Task 1: Upgrade packages, hooks and uv

**Files:**
- Modify: `pyproject.toml` (`[build-system]`, `[dependency-groups]`)
- Modify: `uv.lock`
- Modify: `prek.toml`
- Modify: `.github/workflows/{docs,publish,test}.yml` (`version: 0.11.25`)

- [ ] **Step 1: Bump the dependency-group pins in `pyproject.toml`.** Set each
  `==` pin to the latest PyPI release dated on or before 2026-11-07. Check
  dates with `uvx --from pip pip index versions <pkg>` or the PyPI JSON API.
  Set `zizmor` to `1.32.0` (or later within the cooldown) and set `uv_build` as
  in Global Constraints.
- [ ] **Step 2: Relock.** Run `uvx uv@0.13.7 lock --upgrade`. Expected: exit 0,
  and `uv.lock` changes.
- [ ] **Step 3: Update the hooks.** Run `prek update --freeze`; `cooldown_days = 7`
  applies. Then set the zizmor hook to the same version as Step 1 and
  `minimum_prek_version` to the installed prek version
  (`uv run prek --version`).
- [ ] **Step 4: Set uv to `0.13.7` in all three workflows.**
- [ ] **Step 5: Verify.** Run `uv run tox` and `uv run prek run --all-files`.
  Expected: everything passes. If any zizmor findings appear here, ignore them;
  Task 2 handles them.
- [ ] **Step 6: Commit** `chore(deps): upgrade packages, hooks and uv`.

### Task 2: Actions lockfile and verify workflow

**Files:**
- Modify: all `.github/workflows/*.yml` (`uses:` refs)
- Create: `.github/workflows/lockfile.yml`
- Create: `.github/workflows/actions.lock` (generated, never hand-edited)

**Interfaces:**
- Produces: `lockfile.yml` contains the literal string `--pin v0.4.1`. Task 3's
  Renovate regex matches on it.

- [ ] **Step 1: Bump the actions.** Run `pinact run --update --min-age 7` one
  last time so every action is at its latest version that is at least 7 days
  old.
- [ ] **Step 2: Switch to tag refs.** Rewrite every `uses: owner/repo@<sha> # vX.Y.Z`
  to `uses: owner/repo@vX.Y.Z`. commitizen-action's tags have no `v` prefix,
  for example `@0.27.1`.
- [ ] **Step 3: Create `lockfile.yml`.**
  - Name it `Lockfile` and trigger it on `pull_request` to `main`, with the same
    `concurrency` block as `test.yml` and `permissions: {}`.
  - Add one job, `verify`, that runs on `ubuntu-slim` with
    `permissions: contents: read` and `env: GH_TOKEN: ${{ github.token }}`.
  - Steps: checkout (latest tag, `persist-credentials: false`), then
    `gh extension install github/gh-actions-lock --pin v0.4.1`, then
    `gh actions-lock --verify`.
- [ ] **Step 4: Generate the lockfile.** Run
  `gh extension install github/gh-actions-lock --pin v0.4.1`, then
  `gh actions-lock`. Expected: `✓ All 6 workflows valid` and
  `.github/workflows/actions.lock` created.
- [ ] **Step 5: Verify.** Run `gh actions-lock --verify` and
  `uv run zizmor . --persona auditor`. Expected: both exit 0. Fix any zizmor
  finding in the workflow; never by editing the lockfile.
- [ ] **Step 6: Commit** `ci: lock GitHub Actions with actions.lock`, including
  the workflows and the lockfile.

### Task 3: Renovate config

**Files:**
- Modify: `.github/renovate.json`

**Interfaces:**
- Consumes: the `--pin v0.4.1` string in `.github/workflows/lockfile.yml` from
  Task 2.

- [ ] **Step 1: Edit `renovate.json` to end up with these settings:**
  - `extends: ["config:best-practices", "config:semverAllMonthly"]`. Drop
    `schedule:automergeMonthly`. `semverAllMonthly` already sets the monthly
    schedule.
  - `ignorePresets: ["helpers:pinGitHubActionDigests"]`
  - `minimumReleaseAge: "7 days"`
  - `automerge: false`
  - `nix: { enabled: false }`
  - `lockFileMaintenance: { enabled: true, minimumReleaseAge: null, schedule: ["* 0-3 1 * *"] }`.
    Add a comment saying uv's `exclude-newer` gives the cooldown.
  - `customManagers`: one `regex` entry.
    - `managerFilePatterns: ["/^\\.github/workflows/lockfile\\.yml$/"]`
    - `matchStrings: ["gh-actions-lock --pin (?<currentValue>v\\d+\\.\\d+\\.\\d+)"]`
    - `depNameTemplate: "github/gh-actions-lock"`
    - `datasourceTemplate: "github-releases"`
- [ ] **Step 2: Validate the config.** Run
  `nix shell nixpkgs#renovate -c renovate-config-validator --strict .github/renovate.json`.
  Expected: `Config validated successfully`.
- [ ] **Step 3: Check the resolved config.** Run
  `nix shell nixpkgs#renovate -c renovate --platform=local --dry-run=lookup --print-config 2>&1 | grep -E 'pinGitHubActionDigests|"automerge"'`.
  Expected: no digest-pin preset, and `automerge` false. If a local dry run
  isn't feasible, note it in the commit body.
- [ ] **Step 4: Commit** `ci(renovate): drop digest pins, automerge and nix; fix lock maintenance cooldown`.

### Task 4: Dev tooling, nixpkgs cooldown and README

**Files:**
- Modify: `flake.nix`, `flake.lock`
- Modify: `justfile` (`update` recipe)
- Modify: `README.md` (setup steps)

- [ ] **Step 1: Update `flake.nix`.**
  - Replace `pinact` with `gh` (comment: `# GitHub CLI, used for gh actions-lock`).
  - In `shellHook`, install the extension when it's missing:
    `gh extension list | grep -q gh-actions-lock || gh extension install github/gh-actions-lock --pin v0.4.1`
- [ ] **Step 2: Rewrite the `just update` recipe** as a bash shebang recipe
  with `set -euo pipefail`:

  ```bash
  uv lock --upgrade
  prek update --freeze
  gh actions-lock --relock
  until=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
  sha=$(gh api "repos/NixOS/nixpkgs/commits?sha=nixpkgs-unstable&until=${until}&per_page=1" --jq '.[0].sha')
  nix flake lock --override-input nixpkgs "github:NixOS/nixpkgs/${sha}"
  ```

  Update the recipe comment to:
  `# Update dependencies, hooks, actions lockfile and nix flake (7-day cooldown)`.
- [ ] **Step 3: Run the nix lines from Step 2.** Then check the result:
  `jq '.nodes.nixpkgs.locked.lastModified' flake.lock`. Expected: the timestamp
  is at least 7 days before now
  (`(now - lastModified) >= 604800`).
- [ ] **Step 4: Check the dev shell.** Run
  `nix develop --command gh actions-lock --verify`. Expected: exit 0.
- [ ] **Step 5: Update `README.md`.**
  - Add a step to install gh-actions-lock with
    `gh extension install github/gh-actions-lock`.
  - Add a step to optionally enable the "Require lockfile" Actions policy. Link
    https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies
  - Note that Renovate PRs are merged manually.
- [ ] **Step 6: Commit** `build(nix): replace pinact with gh actions-lock; 7-day nixpkgs cooldown`.

### Final check

- [ ] Run `uv run tox`, `gh actions-lock --verify`,
  `uv run zizmor . --persona auditor` and `uv run prek run --all-files`.
  Expected: all pass.
