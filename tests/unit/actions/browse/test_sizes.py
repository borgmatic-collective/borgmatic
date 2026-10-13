import pytest

from borgmatic.actions.browse import sizes as module


@pytest.mark.parametrize(
    'size,expected',
    (
        (0, '0 B'),
        (1, '1 B'),
        (1023, '1023 B'),
        (1024, '1.0 K'),
        (1536, '1.5 K'),
        (1024 * 1024 - 1, '1.0 M'),
        (1024 * 1024, '1.0 M'),
        (1024**3, '1.0 G'),
        (1024**4, '1.0 T'),
        (1024**5, '1.0 P'),
    ),
)
def test_format_size_formats_size(size, expected):
    assert module.format_size(size) == expected
