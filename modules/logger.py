import logging

def configure_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    if not logger.handlers:  # Prevent adding multiple handlers
        logger.addHandler(handler)

    return logger

logger = configure_logger()