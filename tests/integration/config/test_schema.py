MAXIMUM_LINE_LENGTH = 80


def test_schema_line_length_stays_under_limit():
    schema_file = open('borgmatic/config/schema.yaml')

    for line in schema_file.readlines():
        assert len(line.rstrip('\n')) <= MAXIMUM_LINE_LENGTH
