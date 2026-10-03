# CLAUDE.md

Small Cython 3.0 extension package `fastmath`.

## Layout
- `src/fastmath/_core.pyx` — Cython implementation (all logic lives here)
- `src/fastmath/__init__.py` — re-exports the public API
- `setup.py` — `cythonize` config; `pyproject.toml` — metadata, pins Cython `>=3.0,<3.1`
- `tests/` — pytest suite; `bench.py` — Cython vs pure-Python timing

## Commands
- Build (required after editing any `.pyx`): `pip install -e ".[test]"`
- Test: `python -m pytest -q`
- Benchmark: `python bench.py`

## Notes
- Generated `.c` / `.so` files are gitignored; never commit them.
- `_core.pyx` disables `boundscheck`/`wraparound`; validate inputs explicitly.
- Add any new public function to `__all__` in `__init__.py` and cover it in tests.
