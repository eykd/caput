import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml

import caput


@pytest.fixture
def tmpdir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tdir:
        yield Path(tdir)


@pytest.fixture
def config_data() -> dict[str, Any]:
    return {'foo': {'bar': {'baz': 'blah'}, 'things': [4, 5, 6]}, 'brine': 'salty'}


@pytest.fixture
def defaults() -> dict[str, Any]:
    return {
        'foo': {'bar': {'boo': 'bah'}, 'things': [1, 2, 3], 'banana': 'fruit'},
        'brine': None,
    }


@pytest.fixture
def merged_data() -> dict[str, Any]:
    return {
        'foo': {
            'bar': {'baz': 'blah', 'boo': 'bah'},
            'things': [4, 5, 6],
            'banana': 'fruit',
        },
        'brine': 'salty',
    }


@pytest.fixture
def serialized_data(config_data: dict[str, Any]) -> str:
    return yaml.safe_dump(config_data)


@pytest.fixture
def header(serialized_data: str) -> str:
    return f'---\n{serialized_data}\n---'


@pytest.fixture
def content() -> str:
    return 'blah\n'


@pytest.fixture
def content_bytes() -> bytes:
    return b'\xa01\xa02\xa03\xa04\xa05'


@pytest.fixture
def fp_w_head(tmpdir: Path, header: str, content: str) -> Path:
    fp = tmpdir / 'foo.html'
    fp.write_text(f'{header}\n{content}')
    return fp


@pytest.fixture
def fp_wo_head(tmpdir: Path, content: str) -> Path:
    fp = tmpdir / 'foo.html'
    fp.write_text(f'{content}')
    return fp


@pytest.fixture
def fp_wo_head_bytes(tmpdir: Path, content_bytes: bytes) -> Path:
    fp = tmpdir / 'foo.jpeg'
    fp.write_bytes(content_bytes)
    return fp


@pytest.fixture
def fp_shadow(tmpdir: Path, fp_wo_head_bytes: Path, serialized_data: str) -> Path:
    fp = tmpdir / f'{fp_wo_head_bytes.stem}.yml'
    fp.write_text(serialized_data)
    return fp


def test_it_should_read_config_for_file_with_header(
    fp_w_head: Path, defaults: dict[str, Any], merged_data: dict[str, Any]
) -> None:
    result = caput.read_config(fp_w_head, defaults=defaults)
    assert result == merged_data


def test_it_should_read_config_for_file_wo_header(
    fp_wo_head: Path, defaults: dict[str, Any]
) -> None:
    result = caput.read_config(fp_wo_head, defaults=defaults)
    assert result == defaults


def test_it_should_read_config_for_file_with_shadow_header(
    fp_wo_head_bytes: Path,
    fp_shadow: Path,
    defaults: dict[str, Any],
    merged_data: dict[str, Any],
) -> None:
    result = caput.read_config(fp_wo_head_bytes, defaults=defaults)
    assert result == merged_data


def test_it_should_read_a_config_header(
    fp_w_head: Path,
    config_data: dict[str, Any],
    defaults: dict[str, Any],
    merged_data: dict[str, Any],
) -> None:
    result = caput.read_config_header(fp_w_head, defaults=defaults)
    assert result == merged_data


def test_it_should_return_true_if_a_shadow_config_exists(
    fp_wo_head_bytes: Path, fp_shadow: Path
) -> None:
    assert caput.has_shadow_config(fp_wo_head_bytes) is True


def test_it_should_return_false_if_a_shadow_config_doesnt_exist(
    fp_wo_head_bytes: Path,
) -> None:
    assert caput.has_shadow_config(fp_wo_head_bytes) is False


def test_it_should_read_contents_of_a_file_with_a_header(
    fp_w_head: Path, content: str
) -> None:
    assert caput.read_contents(fp_w_head) == content


def test_it_should_read_contents_of_a_file_with_no_header(
    fp_wo_head: Path, content: str
) -> None:
    assert caput.read_contents(fp_wo_head) == content


def test_it_should_read_byte_contents_of_a_file_with_no_header(
    fp_wo_head_bytes: Path, content_bytes: bytes
) -> None:
    assert caput.read_contents(fp_wo_head_bytes, encoding=None) == content_bytes


def test_it_should_return_true_if_a_file_has_a_header(fp_w_head: Path) -> None:
    assert caput.has_config_header(fp_w_head) is True


def test_it_should_return_false_if_a_file_has_no_header(fp_wo_head: Path) -> None:
    assert caput.has_config_header(fp_wo_head) is False


def test_it_should_return_false_if_a_binary_file_has_no_header(
    fp_wo_head_bytes: Path,
) -> None:
    assert caput.has_config_header(fp_wo_head_bytes) is False


def test_it_should_get_a_shadow_config_name(tmpdir: Path) -> None:
    fp = tmpdir / 'foo.jpeg'
    expected = tmpdir / 'foo.yml'
    result = caput.get_shadow_config_name(fp)
    assert result == expected


def test_it_should_parse_a_config(
    defaults: dict[str, Any], serialized_data: str, merged_data: dict[str, Any]
) -> None:
    result = caput.parse_config(serialized_data, defaults=defaults)
    assert result == merged_data


def test_it_should_return_false_if_file_does_not_exist(tmpdir: Path) -> None:
    nonexistent_file = tmpdir / 'nonexistent.txt'
    assert caput.has_config_header(nonexistent_file) is False


def test_it_should_merge_dicts(
    defaults: dict[str, Any], config_data: dict[str, Any], merged_data: dict[str, Any]
) -> None:
    result = caput.merge_dicts(defaults, config_data)
    assert result == merged_data


class TestIsTextFile:
    def test_markdown_file_is_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.md'
        assert caput.is_text_file(filepath) is True

    def test_json_file_is_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.json'
        assert caput.is_text_file(filepath) is True

    def test_yaml_file_is_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.yml'
        assert caput.is_text_file(filepath) is True

    def test_python_file_is_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.py'
        assert caput.is_text_file(filepath) is True

    def test_image_file_is_not_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.png'
        assert caput.is_text_file(filepath) is False

    def test_unknown_extension_is_not_text(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'test.unknown'
        assert caput.is_text_file(filepath) is False


class TestWriteConfigHeader:
    def test_write_header_to_new_file(
        self, tmpdir: Path, config_data: dict[str, Any]
    ) -> None:
        filepath = tmpdir / 'new.md'
        caput.write_config_header(filepath, config_data)

        assert filepath.exists()
        result = caput.read_config(filepath)
        assert result == config_data

        content = caput.read_contents(filepath)
        assert content == ''

    def test_write_header_to_existing_file_without_header(
        self, tmpdir: Path, config_data: dict[str, Any], content: str
    ) -> None:
        filepath = tmpdir / 'existing.md'
        filepath.write_text(content)

        caput.write_config_header(filepath, config_data)

        result = caput.read_config(filepath)
        assert result == config_data

        result_content = caput.read_contents(filepath)
        assert result_content == content

    def test_write_header_to_existing_file_with_header(
        self, fp_w_head: Path, defaults: dict[str, Any], content: str
    ) -> None:
        new_config = {'new': 'data', 'another': 'value'}
        caput.write_config_header(fp_w_head, new_config)

        result = caput.read_config(fp_w_head)
        assert result == new_config

        result_content = caput.read_contents(fp_w_head)
        assert result_content == content


class TestWriteContents:
    def test_write_plain_text_content(self, tmpdir: Path) -> None:
        filepath = tmpdir / 'plain.txt'
        content = 'This is plain content.'

        caput.write_contents(filepath, content)

        assert filepath.exists()
        result = filepath.read_text()
        assert result == content
        assert not caput.has_config_header(filepath)

    def test_write_text_content_with_config(
        self, tmpdir: Path, config_data: dict[str, Any]
    ) -> None:
        filepath = tmpdir / 'with_config.md'
        content = 'This is content with metadata.'

        caput.write_contents(filepath, content, config=config_data)

        assert filepath.exists()
        result_config = caput.read_config(filepath)
        assert result_config == config_data

        result_content = caput.read_contents(filepath)
        assert result_content == content

    def test_write_binary_content(self, tmpdir: Path, content_bytes: bytes) -> None:
        filepath = tmpdir / 'binary.bin'

        caput.write_contents(filepath, content_bytes, encoding=None)

        assert filepath.exists()
        result = filepath.read_bytes()
        assert result == content_bytes

    def test_write_binary_content_with_config(
        self, tmpdir: Path, content_bytes: bytes, config_data: dict[str, Any]
    ) -> None:
        filepath = tmpdir / 'binary_with_config.bin'

        caput.write_contents(filepath, content_bytes, config=config_data, encoding=None)

        assert filepath.exists()
        result = filepath.read_bytes()
        assert result == content_bytes

        # Should create shadow config
        assert caput.has_shadow_config(filepath)
        result_config = caput.read_config(filepath)
        assert result_config == config_data


class TestWriteConfig:
    def test_write_config_to_new_text_file(
        self, tmpdir: Path, config_data: dict[str, Any]
    ) -> None:
        filepath = tmpdir / 'new.md'

        caput.write_config(filepath, config_data)

        assert filepath.exists()
        assert caput.has_config_header(filepath)
        result = caput.read_config(filepath)
        assert result == config_data

    def test_write_config_to_new_binary_file(
        self, tmpdir: Path, config_data: dict[str, Any]
    ) -> None:
        filepath = tmpdir / 'new.png'

        caput.write_config(filepath, config_data)

        assert filepath.exists()
        assert caput.has_shadow_config(filepath)
        result = caput.read_config(filepath)
        assert result == config_data

    def test_write_config_to_existing_text_file_without_config(
        self, tmpdir: Path, config_data: dict[str, Any], content: str
    ) -> None:
        filepath = tmpdir / 'existing.md'
        filepath.write_text(content)

        caput.write_config(filepath, config_data)

        assert caput.has_config_header(filepath)
        result = caput.read_config(filepath)
        assert result == config_data

        result_content = caput.read_contents(filepath)
        assert result_content == content

    def test_write_config_to_existing_binary_file_without_config(
        self, tmpdir: Path, config_data: dict[str, Any], content_bytes: bytes
    ) -> None:
        filepath = tmpdir / 'existing.png'
        filepath.write_bytes(content_bytes)

        caput.write_config(filepath, config_data)

        assert caput.has_shadow_config(filepath)
        result = caput.read_config(filepath)
        assert result == config_data

        result_content = filepath.read_bytes()
        assert result_content == content_bytes

    def test_write_config_to_existing_file_with_header(
        self, fp_w_head: Path, defaults: dict[str, Any], content: str
    ) -> None:
        new_config = {'updated': 'config', 'new_field': 123}

        caput.write_config(fp_w_head, new_config)

        result = caput.read_config(fp_w_head)
        assert result == new_config

        result_content = caput.read_contents(fp_w_head)
        assert result_content == content

    def test_write_config_to_existing_file_with_shadow_config(
        self, fp_wo_head_bytes: Path, fp_shadow: Path, config_data: dict[str, Any]
    ) -> None:
        new_config = {'updated': 'shadow_config', 'version': 2}

        caput.write_config(fp_wo_head_bytes, new_config)

        result = caput.read_config(fp_wo_head_bytes)
        assert result == new_config

        # Original file content should be unchanged
        original_content = fp_wo_head_bytes.read_bytes()
        assert original_content  # Should still exist
