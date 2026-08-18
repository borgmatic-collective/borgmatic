import json
import logging
import sys

import borgmatic.config.generate
import borgmatic.logger

logger = logging.getLogger(__name__)


def run_show(show_arguments, configs):
    '''
    Given the show arguments as an argparse.Namespace instance and a dict of configuration filename
    to corresponding parsed configuration, run the "show" action. That consists of rendering and
    logging the computed configuration as YAML, separating the configuration for each file with
    "---".

    If show_arguments.option is set, limit the results to the value of that single option. If
    show_arguments.json is True, render the results as JSON with one array element per configuration
    file.
    '''
    borgmatic.logger.add_custom_log_levels()

    if show_arguments.json:
        sys.stdout.write(
            json.dumps(
                [
                    config.get(show_arguments.option) if show_arguments.option else config
                    for config in configs.values()
                ]
            )
        )

        return

    for config in configs.values():
        if len(configs) > 1:
            logger.answer('---')

        logger.answer(
            borgmatic.config.generate.render_configuration(
                config.get(show_arguments.option) if show_arguments.option else config
            ).rstrip()
        )
