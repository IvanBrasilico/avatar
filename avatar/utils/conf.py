"""Define configurações/carrega de arquivo."""
import os

from avatar.utils.logconf import logger

# size = (256, 120)
HOMEDIR = os.getcwd()
IMAGES_FOLDER = os.path.join(HOMEDIR, 'images')
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')
BSON_DIR = os.path.join('.', 'bson')
VIRASANA_URL = 'https://10.68.64.12/virasana/'

CONF_FILE = os.path.join(HOMEDIR, 'avatar.conf')
avatar_conf = {}
try:
    with open(CONF_FILE, 'r') as conf_file:
        for line in conf_file.readlines():
            line_split = line.split('=')
            key = line_split[0].strip()
            value = line_split[1].strip()
            avatar_conf[key] = value
except FileNotFoundError as err:
    logger.error(f'HOMEDIR: {HOMEDIR}')
    logger.error('Arquivo de configuração não encontrado. '
                 'Usando Unidade "ALFSTS".')
    logger.error('Crie arquivo avatar.conf para configurar')
    raise err

BSON_BATCH_SIZE = int(avatar_conf.get('BSON_BATCH_SIZE', 1000))
UNIDADE = avatar_conf.get('UNIDADE', 'ALFSTS')

INTERVALO = int(avatar_conf.get('INTERVALO', 30))
BSON_DIR = avatar_conf.get('BSON_DIR', os.path.join('.', 'bson'))
VIRASANA_URL = avatar_conf.get('VIRASANA_URL', 'https://10.68.64.12/virasana/')
thumb_size_str = avatar_conf.get('THUMB_SIZE')
if thumb_size_str is None:
    THUMB_SIZE = (3000, 1200)
else:
    thumb_size_list = thumb_size_str.split(',')
    THUMB_SIZE = (int(thumb_size_list[0]), int(thumb_size_list[1]))


def get_tags_str(titulo: str, default):
    tags = avatar_conf.get(titulo)
    if tags is None:
        return default
    return tags.split(',')


EXTENSOES_JPG = get_tags_str(
    'EXTENSOES_JPG',
    ['*tamp.jpg', '*thumbxray.jpg', '*icon.jpg', '*-xray.jpg']
)

TAGS_NUMERO = get_tags_str(
    'TAGS_NUMERO',
    ['ContainerId', 'container_no', 'ContainerID1', 'Container1']
)

TAGS_DATA = get_tags_str(
    'TAGS_DATA',
    ['Date', 'SCANTIME', 'ScanTime', 'createdate']
)

if __name__ == '__main__':
    import sys
    confs = dir(sys.modules[__name__])
    for conf in confs:
        if '__' not in conf:
            print(conf,  getattr(sys.modules[__name__], conf))