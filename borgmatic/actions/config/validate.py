import logging

import borgmatic.config.generate
import borgmatic.logger

logger = logging.getLogger(__name__)


def run_validate(validate_arguments, configs):
    '''
    Given the validate arguments as an argparse.Namespace instance and a dict of configuration
    filename to corresponding parsed configuration, run the "validate" action.

    Most of the validation is actually performed implicitly by the standard borgmatic configuration
    loading machinery prior to here, so this function mainly exists to support additional validate
    flags like "--show".
    '''
    borgmatic.logger.add_custom_log_levels()

    if validate_arguments.show:
        for config_path, config in configs.items():
            if len(configs) > 1:
                logger.answer('---')

            logger.answer(borgmatic.config.generate.render_configuration(config))
