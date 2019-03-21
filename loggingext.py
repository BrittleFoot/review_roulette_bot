import logging


def configure_system_logging(logger, config):
    logger.setLevel(logging.DEBUG)

    info_fh = logging.FileHandler(config['info_filename'], encoding='utf-8')
    info_fh.setLevel(logging.INFO)

    debug_fh = logging.FileHandler(config['debug_filename'], encoding='utf-8')
    debug_fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(config['format'])
    info_fh.setFormatter(formatter)
    debug_fh.setFormatter(formatter)

    logger.addHandler(info_fh)
    logger.addHandler(debug_fh)