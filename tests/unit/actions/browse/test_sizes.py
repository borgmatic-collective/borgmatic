import pytest

from borgmatic.actions.browse import sizes as module


@pytest.mark.parametrize(
    'size,expected',
    (
        (0, '0 B'),
        (1, '1 B'),
        (358, '358 B'),
        (999, '999 B'),
        (1000, '1.00 kB'),
        (1024, '1.02 kB'),
        (21600, '21.60 kB'),
        (999999, '1.00 MB'),
        (1000000, '1.00 MB'),
        (8210000000, '8.21 GB'),
        (1480000000000, '1.48 TB'),
    ),
)
def test_format_size_formats_size(size, expected):
    assert module.format_size(size) == expected
