import logging
import os

os.makedirs("logs", exist_ok=True)

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    info_handler = logging.FileHandler(f'logs/{name}_info.log')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(f'logs/{name}_error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.propagate = False  # 🔥 부모 핸들러로 전파 막기 (중복 방지)

    return logger