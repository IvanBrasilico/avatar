"""Este arquivo configura o serviço de log.

Para utilizar, importar variável logger:

from avatar.utils.logconf import logger

Em aplicação de interface texto, setar nível debug:
    console.setLevel(logging.DEBUG)
Para debugar com log arquivo, setar:
    logrotatefile.setLevel(logging.DEBUG)

"""
import logging
from logging.handlers import RotatingFileHandler

LOGFILEMAXBYTES = 10000


def init_log():
    # Log em arquivo
    logrotatefile = RotatingFileHandler('avatar.log', maxBytes=LOGFILEMAXBYTES)
    logrotatefile.setLevel(logging.INFO)

    # Log em stdout
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)

    # Formatação dos logs
    formatter = logging.Formatter(
        fmt='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M')
    console.setFormatter(formatter)
    logrotatefile.setFormatter(formatter)

    # Variável de log padrão
    logger = logging.getLogger('avatar')
    logger.addHandler(console)
    logger.addHandler(logrotatefile)
    return console


logger = logging.getLogger('avatar')
if len(logger.handlers) == 0:
    print('Iniciando logs')
    console = init_log()
