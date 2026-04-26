## 0.3.1 (2026-04-26)

### Fix

- **workflows**: only publish docs on release
- auto open browser on `just docs`
- readme setup script

### Refactor

- split dependency groups and tox environments

### Perf

- better hooks

## 0.3.0 (2026-04-25)

### Feat

- **pre-commit**: add uv-lock to keep uv.lock in sync with pyproject.toml

### Fix

- remove fish from flake.nix, add just dev command
- pin uv in workflows
- pin dev dependencies

## 0.2.1 (2026-04-25)

### Fix

- move prek to pyproject.toml and tox to be managed by uv (for tox-uv)

## 0.2.0 (2026-04-24)

### Feat

- add PyPI publishing
- add exclamation in title on breaking change commit with cz

### Refactor

- improve workflows to use uv

## 0.1.0 (2026-04-23)

### Feat

- initial setup for a python project template
