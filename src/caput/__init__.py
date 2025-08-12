"""Caput: Python library for easy file metadata handling.

This module provides utilities for reading and writing metadata from files using
YAML headers (front matter) or sidecar configuration files. It supports both text
files with YAML headers and binary files with shadow configuration files.

The main entry points are read_config() and write_config() functions which
automatically detect whether to use YAML headers or shadow files.

Example:
    Basic usage for reading and writing file metadata:

    >>> # Reading metadata
    >>> config = read_config('document.md')
    >>> print(config.get('title', 'Untitled'))

    >>> # Writing metadata
    >>> write_config('article.md', {'title': 'My Article', 'author': 'John'})

    With defaults:

    >>> defaults = {'author': 'Unknown', 'draft': False}
    >>> config = read_config('document.md', defaults=defaults)

"""

import mimetypes
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


def is_text_file(filepath: str | Path) -> bool:
    """Determine if a file should be treated as text based on its mimetype.

    Uses the mimetypes library to guess the file type and determines whether
    it should be treated as a text file (suitable for YAML headers) or binary
    file (requiring shadow config files).

    Args:
        filepath: Path to the file to check.

    Returns:
        True if the file should be treated as text, False for binary files.

    Example:
        >>> is_text_file('document.md')  # True
        >>> is_text_file('image.png')  # False
        >>> is_text_file('data.json')  # True

    """
    filepath = Path(filepath)

    # Common text file extensions that mimetypes might not recognize
    text_extensions = {
        '.yml',
        '.yaml',
        '.md',
        '.markdown',
        '.txt',
        '.py',
        '.js',
        '.ts',
        '.css',
        '.html',
        '.htm',
        '.xml',
        '.json',
        '.csv',
        '.ini',
        '.cfg',
        '.conf',
        '.log',
        '.rst',
        '.tex',
        '.sql',
        '.sh',
        '.bash',
        '.zsh',
        '.fish',
        '.ps1',
        '.bat',
        '.cmd',
        '.dockerfile',
        '.gitignore',
        '.gitattributes',
        '.editorconfig',
        '.toml',
        '.lock',
    }

    if filepath.suffix.lower() in text_extensions:
        return True

    mimetype, _ = mimetypes.guess_type(str(filepath))

    if mimetype is None:
        return False

    # Common text file patterns
    text_types = {
        'text/',
        'application/json',
        'application/xml',
        'application/yaml',
        'application/x-yaml',
        'application/javascript',
        'application/typescript',
    }

    return any(mimetype.startswith(prefix) for prefix in text_types)


def write_config(
    filepath: str | Path,
    config: dict[str, Any],
    encoding: str = DEFAULT_ENCODING,
) -> None:
    """Write configuration to file header or shadow file.

    This is the main entry point for writing metadata. It automatically determines
    whether to write as a YAML header (for text files) or as a shadow configuration
    file (for binary files) based on the file type.

    Args:
        filepath: Path to the file to write configuration to.
        config: Configuration data to write.
        encoding: Text encoding to use when writing files.

    Example:
        >>> # For text files, writes YAML header
        >>> write_config('article.md', {'title': 'My Article', 'author': 'John'})

        >>> # For binary files, creates shadow config
        >>> write_config('image.png', {'title': 'Photo', 'date': '2023-01-01'})

    """
    filepath = Path(filepath)

    # Determine write strategy based on existing state and file type
    if filepath.exists():
        if has_config_header(filepath):
            # File exists with header, update it
            write_config_header(filepath, config, encoding=encoding)
        elif has_shadow_config(filepath):
            # File exists with shadow config, update it
            _write_shadow_config(filepath, config, encoding=encoding)
        else:
            # File exists but no config, decide based on file type
            if is_text_file(filepath):
                write_config_header(filepath, config, encoding=encoding)
            else:
                _write_shadow_config(filepath, config, encoding=encoding)
    else:
        # File doesn't exist, decide based on file type
        if is_text_file(filepath):
            write_config_header(filepath, config, encoding=encoding)
        else:
            # Create empty file and shadow config
            filepath.touch()
            _write_shadow_config(filepath, config, encoding=encoding)


def write_config_header(
    filepath: str | Path,
    config: dict[str, Any],
    encoding: str = DEFAULT_ENCODING,
) -> None:
    """Write configuration as YAML header in file.

    Writes YAML front matter to the beginning of a file. If the file already
    has a YAML header, it replaces it. If the file doesn't exist, it creates
    it with the header and empty content.

    Args:
        filepath: Path to the file to write the header to.
        config: Configuration data to write as YAML header.
        encoding: Text encoding to use when writing the file.

    Example:
        >>> # Creates or updates YAML header
        >>> write_config_header(
        ...     'article.md',
        ...     {'title': 'My Article', 'author': 'John Doe', 'date': '2023-01-01'},
        ... )

    """
    filepath = Path(filepath)

    # Get existing content (without header)
    if filepath.exists():
        existing_content = read_contents(filepath, encoding=encoding)
    else:
        existing_content = ''

    # Generate YAML header
    yaml = YAML()
    yaml.width = 4096  # Prevent line wrapping
    yaml.map_indent = 2
    yaml.sequence_indent = 4

    from io import StringIO

    yaml_stream = StringIO()
    yaml.dump(config, yaml_stream)
    yaml_content = yaml_stream.getvalue().strip()

    # Write file with header and content
    with filepath.open('w', encoding=encoding) as fo:
        fo.write('---\n')
        fo.write(yaml_content)
        fo.write('\n---\n')
        if existing_content:
            fo.write(existing_content)


def write_contents(
    filepath: str | Path,
    content: str | bytes,
    config: dict[str, Any] | None = None,
    encoding: str | None = DEFAULT_ENCODING,
) -> None:
    """Write file contents with optional configuration header.

    Writes content to a file, optionally including YAML front matter metadata.
    Supports both text and binary content.

    Args:
        filepath: Path to the file to write.
        content: Content to write to the file.
        config: Optional configuration data to write as YAML header (text files only).
        encoding: Text encoding to use. If None, writes as binary.

    Example:
        >>> # Write text file with header
        >>> write_contents(
        ...     'article.md', 'This is the content.', config={'title': 'My Article'}
        ... )

        >>> # Write plain text file
        >>> write_contents('plain.txt', 'Just content.')

        >>> # Write binary file
        >>> write_contents('data.bin', b'binary data', encoding=None)

    """
    filepath = Path(filepath)

    if encoding is None:
        # Binary mode
        if config is not None:
            # Binary files can't have headers, write shadow config instead
            _write_shadow_config(filepath, config, encoding=DEFAULT_ENCODING)
        with filepath.open('wb') as fo:
            fo.write(content)
    else:
        # Text mode
        if config is not None:
            # Write with YAML header
            yaml = YAML()
            yaml.width = 4096
            yaml.map_indent = 2
            yaml.sequence_indent = 4

            from io import StringIO

            yaml_stream = StringIO()
            yaml.dump(config, yaml_stream)
            yaml_content = yaml_stream.getvalue().strip()

            with filepath.open('w', encoding=encoding) as fo:
                fo.write('---\n')
                fo.write(yaml_content)
                fo.write('\n---\n')
                fo.write(content)
        else:
            # Write plain content
            with filepath.open('w', encoding=encoding) as fo:
                fo.write(content)


def _write_shadow_config(
    filepath: str | Path,
    config: dict[str, Any],
    extension: str = 'yml',
    encoding: str = DEFAULT_ENCODING,
) -> None:
    """Write configuration to shadow config file.

    Internal helper function to write configuration data to a sidecar file.
    Creates a shadow configuration file with the same stem as the original file.

    Args:
        filepath: Path to the primary file.
        config: Configuration data to write.
        extension: File extension for the shadow config file (without dot).
        encoding: Text encoding to use when writing the shadow file.

    """
    shadow_path = get_shadow_config_name(filepath, extension)

    yaml = YAML()
    yaml.width = 4096
    yaml.map_indent = 2
    yaml.sequence_indent = 4

    with shadow_path.open('w', encoding=encoding) as fo:
        yaml.dump(config, fo)
