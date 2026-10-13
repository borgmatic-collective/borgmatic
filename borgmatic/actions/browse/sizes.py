SIZE_UNITS = ('B', 'kB', 'MB', 'GB', 'TB', 'PB')
SIZE_MULTIPLIER = 1000


def format_size(size):
    '''
    Given a size in bytes, return it as a human-readable string like "358 B" or "1.48 TB", using
    decimal units and two decimal places like borg info does.
    '''
    value = float(size)
    unit = SIZE_UNITS[0]

    for next_unit in SIZE_UNITS[1:]:
        # Compare rounded values so that, for instance, 999.999 kB doesn't display as "1000.00 kB".
        if round(value, 2) < SIZE_MULTIPLIER:
            break

        value /= SIZE_MULTIPLIER
        unit = next_unit

    return f'{value:.0f} {unit}' if unit == 'B' else f'{value:.2f} {unit}'
