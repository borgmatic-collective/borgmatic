SIZE_UNITS = ('B', 'K', 'M', 'G', 'T', 'P')
SIZE_MULTIPLIER = 1024


def format_size(size):
    '''
    Given a size in bytes, return it as a compact, human-readable string like "512 B" or "4.0 K",
    using powers of 1024 like du does.
    '''
    value = float(size)
    unit = SIZE_UNITS[0]

    for next_unit in SIZE_UNITS[1:]:
        # Compare rounded values so that, for instance, 1023.99 K doesn't display as "1024.0 K".
        if round(value, 1) < SIZE_MULTIPLIER:
            break

        value /= SIZE_MULTIPLIER
        unit = next_unit

    return f'{int(size)} B' if unit == 'B' else f'{value:.1f} {unit}'
