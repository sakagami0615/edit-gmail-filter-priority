def override(method):
    def _override(*args, **kwargs):
        method(*args, **kwargs)

    return _override
