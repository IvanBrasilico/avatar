"""Script de linha de comando para processar diretório de arquivos BSON.

Script de linha de comando para fazer atualização 'manual'
processando diretório contendo arquivos BSON gerados pelo Avatar

Args:

    --dir: diretório a processar
    --dir: endereço do Servidor Virasana
    --sync: Fazer upload de forma síncrona (True ou False)

"""
import os
import click


from utils.dir_monitor import despacha_dir

BSON_DIR = os.path.join('.', 'bson')
VIRASANA_URL = 'http://10.68.64.12/virasana/'

@click.command()
@click.option('--dir', default=BSON_DIR,
              help='diretório a processar - padrão %s ' % BSON_DIR)
@click.option('--url', default=VIRASANA_URL,
              help='URL do Servidor - padrão %s ' % VIRASANA_URL)
@click.option('--sync', is_flag=True,
              help='Fazer consulta de forma síncrona')
def carrega(dir, url, sync):
    """Script de linha de comando para integração do arquivo XML."""
    print(despacha_dir(dir=dir, url=url, sync=sync))


if __name__ == '__main__':
    carrega()
