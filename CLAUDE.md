# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Caput is a Python library for easy file metadata handling. It supports YAML metadata headers for text files and sidecar "shadow" configuration files for binary files. The project uses modern Python packaging with uv and pyproject.toml.

## Development Commands

### Testing
- `./runtests.sh` - Main test script that runs ruff checks, formatting, and pytest with coverage
- `uv run python -m pytest` - Run tests directly
- `uv run python -m pytest --failed-first --exitfirst` - Run failed tests first and stop on first failure
- `uv run python -m pytest tests/test_caput.py::test_function_name` - Run specific test

### Code Quality
- `uv run ruff check` - Check code style and linting
- `uv run ruff check --fix` - Auto-fix linting issues (ignores T100/breakpoint by default)
- `uv run ruff format` - Format code

### Building and Distribution
- `uv build` - Build the package (uses hatchling backend)
- `uv run twine upload dist/*` - Upload to PyPI (requires twine in dev dependencies)

### Development Environment
- `uv sync --all-groups` - Install development dependencies
- `uv add --dev <package>` - Add development dependency

## Project Architecture

### Core Structure
- `src/caput/__init__.py` - Main module with all core functionality (single-file library)
- `src/caput/_version.py` - Auto-generated version file from git tags
- `tests/test_caput.py` - Comprehensive test suite using pytest fixtures

### Key Functions
The library provides a simple API focused on metadata extraction:

- `read_config(filepath, defaults=None)` - Main entry point, reads YAML metadata from file headers or shadow files
- `read_contents(filepath, encoding=DEFAULT_ENCODING)` - Reads file content, skipping metadata headers
- `has_config_header(filepath)` - Checks if file starts with `---` (YAML front matter)
- `has_shadow_config(filepath)` - Checks for `.yml` sidecar file
- `merge_dicts(dict_a, *others)` - Recursive dictionary merging for config defaults

### Dependencies
- `funcy` - Functional programming utilities for stream processing
- `pyyaml` - YAML parsing for metadata headers
- No CLI dependencies - pure library

### Testing Strategy
Uses pytest with comprehensive fixtures for different file scenarios:
- Files with YAML headers (`---` delimited)
- Files without headers
- Binary files with shadow config files
- Extensive use of temporary directories and fixtures

### Code Style
- Ruff for linting and formatting with extensive rule selection
- 88 character line length
- Single quotes for inline strings, double quotes for docstrings
- F-string formatting preferred
- Type hints not currently used but encouraged for new code

### Version Management
- Uses `uv-dynamic-versioning` to generate versions from git tags
- Version follows PEP 440 format
- No manual version bumping required


## When asked to create new conventions

When asked to create a new convention (`CLAUDE.md`), add a second-level
heading section to this document, `CLAUDE.md`.

* Name the new convention heading with a short, descriptive title.
* Use the first line of the section to elaborate on the "When..." of the heading.
* Use bullet points to organize further details for the convention.
* Use full imperative sentences.
* Keep new conventions short and to the point.
* Use short examples for complex conventions.

## Python code style and quality

When writing or editing Python code (`*.py`), follow these quality standards:

* Use PEP8 style with CamelCase for class names and snake\_case for variables/functions.
* Include type annotations for all functions, methods, and complex structures.
* Add Google Style docstrings to all packages, modules, functions, classes, and methods.
* Run code quality tools:

  * Format: `uv run ruff format`
  * Lint: `uv run ruff check --fix`


## Testing

When writing Python code (`*.py`), follow these testing practices:

* Write tests first for each change using pytest.
* Organize tests in a dedicated `tests/` folder in the project root.
* Name test files by package and module, omitting the root `cloudmarch` package name.

  * Example: `tests/test_config_loader.py` tests `src/cloudmarch/config/loader.py`
* Use descriptive names for test functions and methods.
* Group related tests in test classes.
* Use fixtures for complex setup.
* Aim for 100% test coverage for code under `src/`.
* When writing tests, move common fixtures to `tests/conftest.py`.
* Run tests with `./scripts/runtests.sh` (which accepts normal `pytest` arguments and flags).

  * Example: `./scripts/runtests.sh tests/test_config_loader.py`

## Test organization with classes

When organizing tests in pytest, group related tests using `TestX` classes:

* Use `TestX` classes to group tests for the same module, function, or behavior.
* Name test classes with descriptive titles like `TestGrammarParser` or `TestFileStorage`.
* Do not inherit from `unittest.TestCase` since pytest handles plain classes.
* Place setup and teardown logic in `setup_method` and `teardown_method`.
* Example:
  ```python
  class TestGrammarParser:
      @pytest.fixture
      def parser(self) -> GrammarParser:
          return GrammarParser()

      def test_parses_simple_grammar(self, parser: GrammarParser) -> None:
          result = parser.parse("Begin: hello")
          assert result["Begin"] == ["hello"]
  ```

## Unit testing with pytest

When writing unit tests for Python libraries, follow these pytest best practices:

* Test public APIs and behaviors, not implementation details.
* Focus on testing function contracts: inputs, outputs, and side effects.
* Use pytest's built-in `assert` statements rather than unittest-style assertions.
* Structure tests with arrange-act-assert pattern for clarity.
* Test edge cases: empty inputs, None values, boundary conditions, and error states.
* Use parametrized tests for testing multiple similar cases:
  ```python
  @pytest.mark.parametrize("input_val,expected", [(1, 2), (3, 4)])
  def test_increment(input_val, expected):
      assert increment(input_val) == expected
  ```
* Mock external dependencies using `pytest-mock` or `unittest.mock`.
* Test exception handling explicitly with `pytest.raises()`:
  ```python
  def test_raises_value_error():
      with pytest.raises(ValueError, match="invalid input"):
          parse_config("bad_input")
  ```
* Use fixtures for test data and setup, preferring function-scoped fixtures.
* Test one behavior per test function to maintain clarity and isolation.
* Avoid testing private methods directly; test through public interfaces.
* Do not test third-party library functionality; focus on your code's usage of it.

## Test failure resolution

When tests fail during development, always fix them immediately:

* Stop all development work until failing tests are addressed.
* Identify the root cause of test failures before making changes.
* Fix the underlying issue rather than updating tests to match broken behavior.
* Ensure all tests pass before continuing with new development.
* Run the full test suite after fixes to prevent regression.
* Update mocks, test data, or test logic only when the intended behavior has genuinely changed.
* Never ignore or skip failing tests without explicit justification.

## Variable naming

When naming variables in Python code, follow these naming practices:

* Use concise but descriptive variable names that clearly indicate purpose.
* Avoid single-character names except in the simplest comprehensions.
* Follow snake\_case for all variables and functions.
* Use plural forms for collections and singular for items.
* Prefix boolean variables with verbs like `is_`, `has_`, or `should_`.

## Exception style

When raising exceptions in Python code, follow these practices:

* Do not raise `Exception`, `RuntimeError`, or any built-in base exception.
* Define specific exceptions in `src/cloudmarch/exceptions.py`.
* Use `raise NewError from original_error` for context chaining.
* Avoid interpolated strings in exception messages.
* Attach context as explicit parameters to exception classes.
* Example:

  ```python
  try:
      ...
  except ValueError as exc:
      raise MissingBucketError("S3 bucket missing", bucket_name) from exc
  ```

## TYPE\_CHECKING blocks

When using `TYPE_CHECKING` imports in Python:

* Always include `# pragma: no cover` to exclude them from test coverage.
* Place all type-only imports inside the block.
* Example:

  ```python
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:  # pragma: no cover
      from cloudmarch.config.types import DeployConfig
  ```

## Test coverage pragmas

When writing Python code with untestable defensive programming constructs:

* Use `# pragma: no cover` for lines that cannot be practically tested.
* Use `# pragma: no branch` for branch conditions that cannot be practically tested.
* Apply pragmas to defensive re-raises, impossible conditions, and safety checks.
* Examples:

  ```python
  except DeploymentError:
      raise  # pragma: no cover - defensive re-raise

  if some_impossible_condition:  # pragma: no branch
      raise RuntimeError("This should never happen")

  except Exception as exc:
      if isinstance(exc, SpecificError):  # pragma: no branch
          raise  # pragma: no cover
  ```

## Git commit style

When committing changes to the repository, use conventional commit format:

* Use the format: `<type>(<scope>): <description>`
* Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
* Keep the first line under 50 characters
* Use present tense imperative mood ("add feature" not "added feature")
* Examples:
  * `feat(cli): add new grammar validation command`
  * `fix(storage): handle missing YAML files gracefully`
  * `docs: update installation instructions`
  * `test(grammars): add tests for include functionality`
