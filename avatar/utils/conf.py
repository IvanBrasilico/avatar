"""Define configurações/carrega de arquivo."""
import os

from avatar.utils.logconf import logger

# size = (256, 120)
HOMEDIR = os.getcwd()
IMAGES_FOLDER = os.path.join(HOMEDIR, 'images')
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')
TAGS_NUMERO = ['ContainerId', 'container_no', 'ContainerID1']
TAGS_DATA = ['Date', 'SCANTIME', 'ScanTime']

BSON_DIR = os.path.join('.', 'bson')
VIRASANA_URL = 'http://10.68.64.12/virasana/'

CONF_FILE = os.path.join(HOMEDIR, 'avatar.conf')
avatar_conf = {}
try:
    with open(CONF_FILE, 'r') as conf_file:
        for line in conf_file.readlines():
            line_split = line.split('=')
            avatar_conf[line_split[0]] = line_split[1]
except FileNotFoundError as err:
    logger.error(f'HOMEDIR: {HOMEDIR}')
    logger.error('Arquivo de configuração não encontrado. '
                 'Usando Unidade "ALFSTS".')
    logger.error('Crie arquivo avatar.conf para configurar')
    raise err

BSON_BATCH_SIZE = int(avatar_conf.get('BSON_BATCH_SIZE', 1000))
UNIDADE = avatar_conf.get('UNIDADE', 'ALFSTS')
EXTENSOES_JPG = avatar_conf.get(
    'EXTENSOES_JPG',
    ['*tamp.jpg', '*thumbxray.jpg', '*icon.jpg']
)
INTERVALO = int(avatar_conf.get('INTERVALO', 30))
BSON_DIR = avatar_conf.get('BSON_DIR', os.path.join('.', 'bson'))
VIRASANA_URL = avatar_conf.get('VIRASANA_URL', 'http://10.68.64.12/virasana/')
thumb_size_str = avatar_conf.get('THUMB_SIZE')
if thumb_size_str is None:
    THUMB_SIZE = (800, 600)
else:
    thumb_size_list = thumb_size_str.split(',')
    THUMB_SIZE = (thumb_size_list[0], thumb_size_list[1])
