from borgmatic.commands.completion import flag as module


def test_variants_passes_through_non_list_index_flag_name():
    assert tuple(module.variants('foo')) == ('foo',)


def test_variants_broadcasts_list_index_flag_name_with_a_range_of_indices():
    assert tuple(module.variants('foo[0].bar')) == (
        'foo[0].bar',
        'foo[1].bar',
        'foo[2].bar',
        'foo[3].bar',
        'foo[4].bar',
        'foo[5].bar',
        'foo[6].bar',
        'foo[7].bar',
        'foo[8].bar',
        'foo[9].bar',
    )
