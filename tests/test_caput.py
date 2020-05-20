import tempfile
from pathlib import Path

import pytest
import yaml

import caput


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as tdir:
        yield Path(tdir)


@pytest.fixture
def config_data():
    return {"foo": {"bar": {"baz": "blah"}, "things": [4, 5, 6]}, "brine": "salty"}


@pytest.fixture
def defaults():
    return {
        "foo": {"bar": {"boo": "bah"}, "things": [1, 2, 3], "banana": "fruit"},
        "brine": None,
    }


@pytest.fixture
def merged_data():
    return {
        "foo": {
            "bar": {"baz": "blah", "boo": "bah"},
            "things": [4, 5, 6],
            "banana": "fruit",
        },
        "brine": "salty",
    }


@pytest.fixture
def serialized_data(config_data):
    return yaml.safe_dump(config_data)


@pytest.fixture
def header(serialized_data):
    return f"---\n{serialized_data}\n---" ""


@pytest.fixture
def content():
    return "blah\n"


@pytest.fixture
def content_bytes():
    return b"\xa01\xa02\xa03\xa04\xa05"


@pytest.fixture
def fp_w_head(tmpdir, header, content):
    fp = tmpdir / "foo.html"
    fp.write_text(f"{header}\n{content}")
    return fp


@pytest.fixture
def fp_wo_head(tmpdir, content):
    fp = tmpdir / "foo.html"
    fp.write_text(f"{content}")
    return fp


@pytest.fixture
def fp_wo_head_bytes(tmpdir, content_bytes):
    fp = tmpdir / "foo.jpeg"
    fp.write_bytes(content_bytes)
    return fp


@pytest.fixture
def fp_shadow(tmpdir, fp_wo_head_bytes, serialized_data):
    fp = tmpdir / f"{fp_wo_head_bytes.stem}.yml"
    fp.write_text(serialized_data)
    return fp


def test_it_should_read_config_for_file_with_header(fp_w_head, defaults, merged_data):
    result = caput.read_config(fp_w_head, defaults=defaults)
    assert result == merged_data


def test_it_should_read_config_for_file_wo_header(fp_wo_head, defaults):
    result = caput.read_config(fp_wo_head, defaults=defaults)
    assert result == defaults


def test_it_should_read_config_for_file_with_shadow_header(
    fp_wo_head_bytes, fp_shadow, defaults, merged_data
):
    result = caput.read_config(fp_wo_head_bytes, defaults=defaults)
    assert result == merged_data


def test_it_should_read_a_config_header(fp_w_head, config_data, defaults, merged_data):
    result = caput.read_config_header(fp_w_head, defaults=defaults)
    assert result == merged_data


def test_it_should_return_true_if_a_shadow_config_exists(fp_wo_head_bytes, fp_shadow):
    assert caput.has_shadow_config(fp_wo_head_bytes) is True


def test_it_should_return_false_if_a_shadow_config_doesnt_exist(fp_wo_head_bytes):
    assert caput.has_shadow_config(fp_wo_head_bytes) is False


def test_it_should_read_contents_of_a_file_with_a_header(fp_w_head, content):
    assert caput.read_contents(fp_w_head) == content


def test_it_should_read_contents_of_a_file_with_no_header(fp_wo_head, content):
    assert caput.read_contents(fp_wo_head) == content


def test_it_should_read_byte_contents_of_a_file_with_no_header(
    fp_wo_head_bytes, content_bytes
):
    assert caput.read_contents(fp_wo_head_bytes, encoding=None) == content_bytes


def test_it_should_return_true_if_a_file_has_a_header(fp_w_head):
    assert caput.has_config_header(fp_w_head) is True


def test_it_should_return_false_if_a_file_has_no_header(fp_wo_head):
    assert caput.has_config_header(fp_wo_head) is False


def test_it_should_return_false_if_a_binary_file_has_no_header(fp_wo_head_bytes):
    assert caput.has_config_header(fp_wo_head_bytes) is False


def test_it_should_get_a_shadow_config_name(tmpdir):
    fp = tmpdir / "foo.jpeg"
    expected = tmpdir / "foo.yml"
    result = caput.get_shadow_config_name(fp)
    assert result == expected


def test_it_should_parse_a_config(defaults, serialized_data, merged_data):
    result = caput.parse_config(serialized_data, defaults=defaults)
    assert result == merged_data


def test_it_should_merge_dicts(defaults, config_data, merged_data):
    result = caput.merge_dicts(defaults, config_data)
    assert result == merged_data
