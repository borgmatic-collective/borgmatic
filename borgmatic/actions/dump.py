import borgmatic.hooks.dispatch


class Dump_cleanup:
    '''
    A Python context manager for removing data source dumps before and after wrapped code. Besides
    doing this for general filesystem cleanliness reasons, leaving old dumps lying around can
    prevent future dumping from working (in the case of filesystem snapshots) or cause Borg hangs
    (in the case of database dump named pipes).

    Example use as a context manager:

        with borgmatic.actions.dump.Dump_cleanup(
            config, borgmatic_runtime_directory, patterns, dry_run,
        ):
            do_something_like_perform_a_dump_or_restore()
    '''

    def __init__(self, config, borgmatic_runtime_directory, patterns, dry_run):
        '''
        Given a configuration dict, the borgmatic runtime directory, the configured patterns, and
        whether this is a dry-run, store these values for use below.
        '''
        self.config = config
        self.borgmatic_runtime_directory = borgmatic_runtime_directory
        self.patterns = patterns
        self.dry_run = dry_run

    def __enter__(self):
        '''
        Remove all data source dumps that exist prior to the wrapped code running.
        '''
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            self.config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            self.borgmatic_runtime_directory,
            self.patterns,
            self.dry_run,
        )

    def __exit__(self, exception_type, exception, traceback):
        '''
        Remove all data source dumps, including any created by the wrapped code.
        '''
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            self.config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            self.borgmatic_runtime_directory,
            self.patterns,
            self.dry_run,
        )
