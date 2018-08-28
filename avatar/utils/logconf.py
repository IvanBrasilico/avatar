import os
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/avatar.log',
                    filemode='w')

console = logging.StreamHandler()
DEBUG = os.environ('DEBUG')
if DEBUG:
    console.setLevel(logging.WARNING)
else:
    console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)

logger = logging.getLogger('avatar')
logger.addHandler(console)
