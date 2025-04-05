import logging

IS_A_HOOK = False
PAYLOAD_TRUNCATION_INDICATOR = '...\n'


class Forgetful_buffering_handler(logging.Handler):
    '''
    A buffering log handler that stores log messages in memory, and throws away messages (oldest
    first) once a particular capacity in bytes is reached. But if the given byte capacity is zero,
    don't throw away any messages.

    The given identifier is used to distinguish the instance of this handler used for one monitoring
    hook from those instances used for other monitoring hooks.
    '''

    def __init__(self, identifier, byte_capacity, log_level):
        super().__init__()

        self.identifier = identifier
        self.byte_capacity = byte_capacity
        self.byte_count = 0
        self.buffer = []
        self.forgot = False
        self.setLevel(log_level)

    def emit(self, record):
        message = record.getMessage() + '\n'
        self.byte_count += len(message)
        self.buffer.append(message)

        if not self.byte_capacity:
            return

        while self.byte_count > self.byte_capacity and self.buffer:
            self.byte_count -= len(self.buffer[0])
            self.buffer.pop(0)
            self.forgot = True


def add_handler(handler):
    '''
    Add the given handler to the global logger.
    '''
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(min(handler.level for handler in logger.handlers))


def get_handler(identifier):
    '''
    Given the identifier for an existing Forgetful_buffering_handler instance, return the handler.

    Raise ValueError if the handler isn't found.
    '''
    try:
        return next(
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, Forgetful_buffering_handler) and handler.identifier == identifier
        )
    except StopIteration:
        raise ValueError(f'A buffering handler for {identifier} was not found')


def format_buffered_logs_for_payload(identifier):
    '''
    Get the handler previously added to the root logger, and slurp buffered logs out of it to
    send to the monitoring service.
    '''
    try:
        buffering_handler = get_handler(identifier)
    except ValueError:
        # No handler means no payload.
        return ''

    payload = ''.join(message for message in buffering_handler.buffer)

    if buffering_handler.forgot:
        return PAYLOAD_TRUNCATION_INDICATOR + payload

    return payload


def remove_handler(identifier):
    '''
    Given the identifier for an existing Forgetful_buffering_handler instance, remove it.
    '''
    logger = logging.getLogger()

    try:
        logger.removeHandler(get_handler(identifier))
    except ValueError:
        pass

    logger.setLevel(min(handler.level for handler in logger.handlers))
