import logging


def run_browse(
    diff_arguments,
    global_arguments,
    configs,
):
    '''
    Run the "browse" action for the given repository.
    '''
    if not configs:
        return

    logging.getLogger('asyncio').setLevel(logging.WARNING)

    try:
        import textual
    except ImportError:  # pragma: no cover
        raise ValueError(
            'Unable to import the Textual library for the browse action; try installing "borgmatic[browse]"'
        )

    import borgmatic.actions.browse.view

    app = borgmatic.actions.browse.view.Browse_app(configs)
    app.run()
