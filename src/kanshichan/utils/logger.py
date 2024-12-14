import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s'
        )
    
    return logger
