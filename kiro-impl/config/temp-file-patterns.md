# Temporary File Patterns

Files matching these patterns are treated as **temporary/generated** and must NOT block execution, boundary checks, or review verdicts.

Agents using kiro-impl must read this file during Preflight and pass its contents to reviewer sub-agents.

## Build Outputs
```
dist/
build/
.next/
out/
target/
__pycache__/
*.pyc
*.pyo
*.class
```

## Test & Tool Caches
```
.pytest_cache/
.mypy_cache/
.ruff_cache/
coverage/
.coverage
htmlcov/
.tox/
node_modules/.cache/
.turbo/
```

## IDE & OS Artifacts
```
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db
desktop.ini
```

## Auto-Updated Lock Files
These files may change as a side effect of dependency resolution without being directly edited:
```
uv.lock
poetry.lock
package-lock.json
yarn.lock
pnpm-lock.yaml
Cargo.lock
go.sum
```

## How to Use (for agents)

1. Read this file at Preflight: `kiro-impl/config/temp-file-patterns.md`
2. Store the full pattern list as `TEMP_PATTERNS`
3. When unexpected diffs appear:
   - If path matches a pattern in `TEMP_PATTERNS` → **ignore and continue** (do not stage, do not stop)
   - If path does NOT match → stop and report to the user for triage
4. When dispatching the reviewer, pass `TEMP_PATTERNS` so boundary checks correctly exclude these files

## Customizing Patterns

To add project-specific temporary patterns, append them below this line with a comment explaining why:

<!-- Project-specific additions below this line -->
