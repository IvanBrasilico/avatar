"""Define configurações/carrega de arquivo."""
import os

from avatar.utils.logconf import logger

# size = (256, 120)
HOMEDIR = os.getcwd()
IMAGES_FOLDER = os.path.join(HOMEDIR, 'images')
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')
TAGS_NUMERO = ['ContainerId', 'container_no', 'ContainerID1']
TAGS_DATA = ['Date', 'SCANTIME', 'ScanTime']

CONF_FILE = os.path.join(HOMEDIR, 'avatar.conf')
avatar_conf = {}
try:
    with open(CONF_FILE, 'r') as conf_file:
        for line in conf_file.readlines():
            line_split = line.split('=')
            avatar_conf[line_split[0]] = line_split[1]
    BSON_BATCH_SIZE = avatar_conf.get('BSON_BATCH_SIZE')
    if BSON_BATCH_SIZE is None:
        BSON_BATCH_SIZE = 1000
    else:
        BSON_BATCH_SIZE = int(BSON_BATCH_SIZE)
    UNIDADE = avatar_conf.get('UNIDADE')
    if UNIDADE is None:
        UNIDADE = 'ALFSTS'
    EXTENSOES_JPG = avatar_conf.get('EXTENSOES_JPG')
    if EXTENSOES_JPG is None:
        EXTENSOES_JPG = ['*mp.jpg', '*thumbxray.jpg', '*icon.jpg']
    INTERVALO = avatar_conf.get('INTERVALO')
    if INTERVALO is None:
        INTERVALO = 30
except FileNotFoundError as err:
    logger.error(f'HOMEDIR: {HOMEDIR}')
    logger.error('Arquivo de configuração não encontrado. '
                 'Usando Unidade "ALFSTS".')
    logger.error('Crie arquivo avatar.conf para configurar')
    raise err
