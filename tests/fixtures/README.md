# tests/fixtures/

Builders for the synthetic test repos used by the test suite. The built repos (with `.git` directories) are gitignored and rebuilt on demand by `conftest.py`.

## Files

| File | What it does |
|---|---|
| `build_mini_pkg.py` | Builds two fixture repos from scratch. `mini_pkg`: 3 core modules, a `setup.py` manifest with one small third-party dep, real pytest tests covering some functions, and 12 commits including a bugfix (test added in the same commit), a dependency change, a docs-only commit, a refactor, a file rename, and a two-commit PR branch merged with `--no-ff`. `mini_pkg_notests`: same shape, no tests, no manifest, imports third-party modules (one alias-mapped) so the AST-inferred-deps path has work to do |
| `__init__.py` | Package docstring |

## Generated directories (not committed)

| Directory | What it is |
|---|---|
| `mini_pkg/` | A real git repo with reproducible history. Rebuilt by `build_mini_pkg.build_mini_pkg()` |
| `mini_pkg_notests/` | Same structure, no tests/manifest. Rebuilt by `build_mini_pkg.build_mini_pkg_notests()` |

These directories are listed in `.gitignore`. They are rebuilt automatically when a test session starts and they don't exist (see `conftest.py`). You can also rebuild manually:

```
python tests/fixtures/build_mini_pkg.py
```
