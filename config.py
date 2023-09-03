import json
import logging
from os import makedirs
from os.path import join
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

# read config file
with open('config.json') as f:
    config = json.load(f)

# initialize constants
ALLOWED_ACCOUNTS: dict = config.get('imap_allowed_accounts', {})
LOG: str = config.get('log', '/var/log/pasarela')
STORAGE: str = config.get('imap_storage', '/tmp/pasarela')
PAGE_SIZE: int = config.get('imap_default_page_size')

makedirs(LOG, exist_ok=True)
makedirs(STORAGE, exist_ok=True)

# logging
log_path = join(LOG, 'imap.log')
log_format = '%(asctime)s %(levelname) %(message)s'

print(log_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(threadName)s %(levelname)s: %(message)s",
    handlers=[
        StreamHandler(),
        RotatingFileHandler(log_path, maxBytes=32*1024*1024, backupCount=10),
    ])
