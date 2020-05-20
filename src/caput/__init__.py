from collections.abc import Mapping
from pathlib import Path

import funcy as fn

import yaml

from ._version import get_versions

__version__ = get_versions()["version"]

del get_versions


DEFAULT_ENCODING = "utf-8"


def read_config(filepath, defaults=None, encoding=DEFAULT_ENCODING):
    if has_shadow_config(filepath):
        return parse_config(
            get_shadow_config_name(filepath).read_text(encoding=encoding),
            defaults=defaults,
        )
    else:
        return read_config_header(filepath, defaults=defaults, encoding=encoding)


def read_config_header(filepath, defaults=None, encoding=DEFAULT_ENCODING):
    filepath = Path(filepath)
    if not has_config_header(filepath):
        return defaults.copy() if defaults else {}
    else:
        with open(filepath, mode="r", encoding=DEFAULT_ENCODING) as fi:
            header = "".join(
                fn.takewhile(
                    fn.none_fn(
                        fn.rpartial(str.startswith, "---\n"),
                        fn.rpartial(str.startswith, "...\n"),
                    ),
                    fn.rest(fi),
                )
            )
        return parse_config(header, defaults)


def read_contents(filepath, encoding=DEFAULT_ENCODING):
    filepath = Path(filepath)
    if not has_config_header(filepath):
        if encoding is None:
            with open(filepath, mode="rb") as fi:
                return fi.read()
        else:
            with open(filepath, mode="r", encoding=encoding) as fi:
                return fi.read()
    else:
        with open(filepath, mode="r", encoding=encoding) as fi:
            return "".join(
                fn.rest(
                    fn.dropwhile(
                        fn.none_fn(
                            fn.rpartial(str.startswith, "---\n"),
                            fn.rpartial(str.startswith, "...\n"),
                        ),
                        fn.rest(fi),
                    )
                )
            )


def has_config_header(filepath):
    filepath = Path(filepath)
    if filepath.is_file():
        with open(filepath, mode="rb") as fi:
            return fi.read(3) == b"---"
    else:
        return False


def has_shadow_config(filepath, extension="yml"):
    sh_filepath = get_shadow_config_name(filepath, extension)
    return sh_filepath.exists()


def get_shadow_config_name(filepath, extension="yml"):
    filepath = Path(filepath)
    return filepath.parent / f"{filepath.stem}.{extension}"


def parse_config(text, defaults=None):
    config = yaml.safe_load(text) or {}
    return merge_dicts(defaults, config) if defaults else config


def merge_dicts(dict_a, *others):
    """Recursive dictionary merge.

    Inspired by :meth:``dict.update()``, instead of updating only top-level
    keys, merge_dicts recurses down into dicts nested to an arbitrary depth,
    updating keys. The ``dict_b`` is merged into ``dict_a``.

    Based on https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    :param dict_a: dict onto which the merge is executed
    :param dict_b: dict_a merged into dict_a
    :return: None

    """
    dict_a = dict_a.copy()
    for dict_b in others:
        for key in dict_b.keys():
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
