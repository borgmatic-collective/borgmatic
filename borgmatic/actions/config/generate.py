import logging

import borgmatic.config.generate
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_generate(generate_arguments, global_arguments):
    dry_run_label = ' (dry run; not actually writing anything)' if global_arguments.dry_run else ''

    logger.answer(
        f'Generating a configuration file at: {generate_arguments.destination_filename}{dry_run_label}'
    )

    borgmatic.config.generate.generate_sample_configuration(
        global_arguments.dry_run,
        generate_arguments.source_filename,
        generate_arguments.destination_filename,
        borgmatic.config.validate.schema_filename(),
        overwrite=generate_arguments.overwrite,
    )

    if generate_arguments.source_filename:
        logger.answer(
            f'''
Merged in the contents of configuration file at: {generate_arguments.source_filename}
To review the changes made, run:

    diff --unified {generate_arguments.source_filename} {generate_arguments.destination_filename}'''
        )

    logger.answer(
        '''
This includes all available configuration options with example values, the few
required options as indicated. Please edit the file to suit your needs.

If you ever need help: https://torsion.org/borgmatic/#issues'''
    )
