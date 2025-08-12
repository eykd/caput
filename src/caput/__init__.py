"""Caput: Python library for easy file metadata handling.

This module provides utilities for reading metadata from files using YAML headers
(front matter) or sidecar configuration files. It supports both text files with
YAML headers and binary files with shadow configuration files.

The main entry point is the read_config() function which automatically detects
whether to read from a YAML header or a shadow file.

Example:
    Basic usage for reading file metadata:

    >>> config = read_config('document.md')
    >>> print(config.get('title', 'Untitled'))

    With defaults:

    >>> defaults = {'author': 'Unknown', 'draft': False}
    >>> config = read_config('document.md', defaults=defaults)

"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import funcy as fn
from ruamel.yaml import YAML

try:
    from . import _version

    __version__ = _version.version
except (ImportError, AttributeError):  # pragma: no cover
    import importlib.metadata

    try:
        __version__ = importlib.metadata.version(__name__)
    except importlib.metadata.PackageNotFoundError:
        __version__ = '0.0.0'

DEFAULT_ENCODING = 'utf-8'


def read_config(
    filepath: str | Path,
    defaults: dict[str, Any] | None = None,
    encoding: str = DEFAULT_ENCODING,
) -> dict[str, Any]:
    """Read configuration from file header or shadow file.

    This is the main entry point for reading metadata. It automatically detects
    whether to read from a YAML header in the file or from a shadow configuration
    file (e.g., document.yml for document.pdf).

    Args:
        filepath: Path to the file to read configuration from.
        defaults: Default configuration values to merge with the loaded config.
        encoding: Text encoding to use when reading files.

    Returns:
        Dictionary containing the merged configuration data.

    Example:
        >>> config = read_config('article.md', defaults={'author': 'Unknown'})
        >>> print(config['title'])  # From YAML header
        >>> print(config['author'])  # From defaults if not in header

    """
    if has_shadow_config(filepath):
        return parse_config(
            get_shadow_config_name(filepath).read_text(encoding=encoding),
            defaults=defaults,
        )
    return read_config_header(filepath, defaults=defaults, encoding=encoding)


def read_config_header(
    filepath: str | Path,
    defaults: dict[str, Any] | None = None,
    encoding: str = DEFAULT_ENCODING,
) -> dict[str, Any]:
    """Read configuration from YAML header in file.

    Reads YAML front matter from the beginning of a file. The YAML header
    must start with '---' and end with '---' or '...'.

    Args:
        filepath: Path to the file to read the header from.
        defaults: Default configuration values to merge with the loaded config.
        encoding: Text encoding to use when reading the file.

    Returns:
        Dictionary containing the merged configuration data from the header.
        If no header exists, returns a copy of defaults or empty dict.

    Example:
        >>> # For a file starting with:
        >>> # ---
        >>> # title: My Article
        >>> # author: John Doe
        >>> # ---
        >>> config = read_config_header('article.md')
        >>> print(config['title'])  # 'My Article'

    """
    filepath = Path(filepath)
    if not has_config_header(filepath):
        return defaults.copy() if defaults else {}
    with filepath.open(encoding=encoding) as fi:
        header = ''.join(
            fn.takewhile(
                fn.none_fn(
                    fn.rpartial(str.startswith, '---\n'),
                    fn.rpartial(str.startswith, '...\n'),
                ),
                fn.rest(fi),
            )
        )
    return parse_config(header, defaults)


def read_contents(
    filepath: str | Path, encoding: str | None = DEFAULT_ENCODING
) -> str | bytes:
    """Read file contents, skipping any YAML header.

    Reads the content of a file while automatically skipping over any YAML
    front matter header. This is useful when you want the actual content
    without the metadata.

    Args:
        filepath: Path to the file to read contents from.
        encoding: Text encoding to use when reading the file. If None, reads
            as binary and returns bytes.

    Returns:
        File contents as string (if encoding specified) or bytes (if encoding is None).
        YAML header is automatically excluded from the returned content.

    Example:
        >>> # For a file with YAML header followed by content
        >>> content = read_contents('article.md')
        >>> print(content)  # Only the content after the header

        >>> # Read as binary
        >>> binary_content = read_contents('image.jpg', encoding=None)
        >>> isinstance(binary_content, bytes)  # True

    """
    filepath = Path(filepath)
    if not has_config_header(filepath):
        if encoding is None:
            with filepath.open(mode='rb') as fi:
                return fi.read()
        else:
            with filepath.open(encoding=encoding) as fi:
                return fi.read()
    else:
        with filepath.open(encoding=encoding) as fi:
            return ''.join(
                fn.rest(
                    fn.dropwhile(
                        fn.none_fn(
                            fn.rpartial(str.startswith, '---\n'),
                            fn.rpartial(str.startswith, '...\n'),
                        ),
                        fn.rest(fi),
                    )
                )
            )


def has_config_header(filepath: str | Path) -> bool:
    """Check if file starts with YAML front matter delimiter.

    Determines whether a file has a YAML header by checking if it starts
    with the standard front matter delimiter '---'.

    Args:
        filepath: Path to the file to check.

    Returns:
        True if the file exists and starts with '---', False otherwise.

    Example:
        >>> has_config_header('article.md')  # True if starts with ---
        >>> has_config_header('plain.txt')  # False if no header

    """
    filepath = Path(filepath)
    if filepath.is_file():
        with filepath.open(mode='rb') as fi:
            return fi.read(3) == b'---'
    else:
        return False


def has_shadow_config(filepath: str | Path, extension: str = 'yml') -> bool:
    """Check if shadow config file exists.

    Checks for the existence of a sidecar configuration file with the same
    base name as the given file but with a different extension (default: .yml).
    This is useful for binary files that cannot contain YAML headers.

    Args:
        filepath: Path to the primary file to check for a shadow config.
        extension: File extension for the shadow config file (without dot).

    Returns:
        True if the shadow configuration file exists, False otherwise.

    Example:
        >>> # Checks for document.yml alongside document.pdf
        >>> has_shadow_config('document.pdf')
        >>> # Checks for image.json alongside image.png
        >>> has_shadow_config('image.png', extension='json')

    """
    sh_filepath = get_shadow_config_name(filepath, extension)
    return sh_filepath.exists()


def get_shadow_config_name(filepath: str | Path, extension: str = 'yml') -> Path:
    """Get the path for a shadow configuration file.

    Constructs the path for a sidecar configuration file based on the given
    file path and extension. The shadow config file has the same stem (name
    without extension) as the original file.

    Args:
        filepath: Path to the primary file.
        extension: File extension for the shadow config file (without dot).

    Returns:
        Path object for the shadow configuration file.

    Example:
        >>> get_shadow_config_name('document.pdf')
        PosixPath('document.yml')
        >>> get_shadow_config_name('image.png', 'json')
        PosixPath('image.json')

    """
    filepath = Path(filepath)
    return filepath.parent / f'{filepath.stem}.{extension}'


def parse_config(text: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    r"""Parse YAML configuration text and merge with defaults.

    Parses a YAML string and merges the result with default values if provided.
    Uses safe YAML loading to prevent code execution vulnerabilities.

    Args:
        text: YAML text to parse.
        defaults: Default configuration values to merge with parsed config.

    Returns:
        Dictionary containing the merged configuration data.

    Example:
        >>> yaml_text = 'title: My Article\\nauthor: John'
        >>> parse_config(yaml_text, defaults={'draft': False})
        {'title': 'My Article', 'author': 'John', 'draft': False}

    """
    yaml = YAML(typ='safe', pure=True)
    config = yaml.load(text) or {}
    return merge_dicts(defaults, config) if defaults else config


def merge_dicts(
    dict_a: dict[str, Any] | None, *others: dict[str, Any]
) -> dict[str, Any]:
    """Recursive dictionary merge.

    Inspired by dict.update(), instead of updating only top-level keys,
    merge_dicts recurses down into dicts nested to an arbitrary depth,
    updating keys. Each dict in others is merged into dict_a.

    Based on https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    Args:
        dict_a: Base dictionary onto which the merge is executed. Can be None.
        *others: Additional dictionaries to merge into dict_a.

    Returns:
        New dictionary containing the merged configuration data.

    Example:
        >>> base = {'a': 1, 'nested': {'x': 10}}
        >>> override = {'b': 2, 'nested': {'y': 20}}
        >>> result = merge_dicts(base, override)
        >>> result
        {'a': 1, 'b': 2, 'nested': {'x': 10, 'y': 20}}

    """
    dict_a = dict_a.copy() if dict_a else {}
    for dict_b in others:
        for key in dict_b:
            value_is_mapping = (
                key in dict_a
                and isinstance(dict_a[key], dict)
                and isinstance(dict_b[key], Mapping)
            )
            if value_is_mapping:
                dict_a[key] = merge_dicts(dict_a[key], dict_b[key])
            else:
                dict_a[key] = dict_b[key]

    return dict_a
