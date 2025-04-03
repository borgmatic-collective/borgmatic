def variants(flag_name):
    '''
    Given a flag name as a string, yield it and any variations that should be complete-able as well.
    For instance, for a string like "--foo[0].bar", yield "--foo[0].bar", "--foo[1].bar", ...,
    "--foo[9].bar".
    '''
    if '[0]' in flag_name:
        for index in range(0, 10):
            yield flag_name.replace('[0]', f'[{index}]')

        return

    yield flag_name
