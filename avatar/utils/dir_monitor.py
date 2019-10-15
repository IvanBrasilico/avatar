"""
Monitora um diretório e envia arquivos BSON nele para o virasana.

USAGE
python dir_monitor.py

A cada intervalo de tempo configurado, lista os arquivos do diretório BSON_DIR
Se houverem arquivos, envia via POST para o endereco VIRASANA_URL

Pode ser importado e rodado em uma tarefa periódica (celery, cron, etc)

"""
import json
import os
import time
from sys import platform
from threading import Thread

import requests
from celery import states
from avatar.utils.logconf import logger

VIRASANA_URL = 'http://localhost:5001'

LOGIN_URL = VIRASANA_URL + '/login'
API_URL = VIRASANA_URL + '/api/uploadbson'
if platform == 'win32':  # I am on ALFSTS???
    BSON_DIR = os.path.join('P:', 'SISTEMAS', 'roteiros', 'AJNA', 'BSON_IVAN')
else:
    BSON_DIR = os.path.join('/home', 'ajna', 'Downloads', 'BSON')

SYNC = True


def get_token(url):
    """Recupera o token CRSF necessário para fazer POST."""
    response = requests.get(url)
    csrf_token = response.text
    print(csrf_token)
    begin = csrf_token.find('csrf_token"') + 10
    end = csrf_token.find('username"') - 10
    csrf_token = csrf_token[begin: end]
    begin = csrf_token.find('value="') + 7
    end = csrf_token.find('/>')
    csrf_token = csrf_token[begin: end]
    print('****', csrf_token)
    return csrf_token


def login(username='ajna', senha='ajna'):
    """Efetua login no servidor."""
    token = get_token(LOGIN_URL)
    return requests.post(LOGIN_URL, data=dict(
        username=username,
        senha=senha,
        csrf_token=token
    ))


def despacha(filename, url=API_URL, sync=SYNC):
    """Envia por HTTP POST o arquivo especificado.

    Args:
        file: caminho completo do arquivo a enviar

        target: URL do Servidor e API destino

    Returns:
        (Erro, Resposta)
        (True, None) se tudo correr bem
        (False, response) se ocorrer erro

    """
    bson = open(filename, 'rb')
    files = {'file': bson}
    # login()
    print('Enviando BSON %s para %s' % (filename, url))
    rv = requests.post(url, files=files, data={'sync': sync}, verify=False)
    if rv is None:
        return False, None
    try:
        response_json = rv.json()
        success = response_json.get('success', False) and \
            (rv.status_code == requests.codes.ok)
    except json.decoder.JSONDecodeError as err:
        logger.error(err, exc_info=True)
        success = False
    return success, rv


def despacha_dir(dir=BSON_DIR, url=API_URL, sync=SYNC):
    """Envia por HTTP POST todos os arquivos do diretório.

    Args:
        dir: caminho completo do diretório a pesquisar

        target: URL do Servidor e API destino

    Returns:
        diretório usado, lista de erros, lista de exceções

    """
    erros = []
    sucessos = []
    exceptions = []
    # Limitar a cinco arquivos por rodada!!!
    cont = 0
    if not os.path.exists(dir):
        return dir, ['Diretório não encontrado'], []
    for filename in os.listdir(dir)[:90]:
        try:
            bsonfile = os.path.join(dir, filename)
            success, response = despacha(bsonfile,
                                         url + '/api/uploadbson', sync)
            if success:
                # TODO: save on database list of files to delete
                #  (if light goes out or system fail, continue)
                response_json = response.json()
                if sync:
                    if response_json.get('success', False) is True:
                        os.remove(bsonfile)
                        print('Arquivo ' + bsonfile + ' removido.')
                        cont += 1
                        print('********* %s' % cont)
                else:
                    taskid = response_json.get('taskid', '')
                    sucessos.append(taskid)
                    Thread(target=espera_resposta,
                           args=(url + '/api/task/' + taskid, bsonfile)
                           ).start()
            else:
                erros.append(response)
                print(response.text)
        except Exception as err:
            exceptions.append(err)
            print(err, exc_info=True)
    return dir, erros, exceptions


def espera_resposta(api_url, bson_file, sleep_time=10, timeout=180):
    """Espera resposta da task.

    Espera resposta da task que efetivamente carregará o arquivo no
    Banco de Dados do Servidor.
    Recebendo uma resposta positiva, exclui arquivo enviado do disco.
    Recebendo uma resposta negativa, grava no logger.

    Args:
        api_url: endereço para acesso aos dados da task

        bson_file: caminho completo do arquivo original que foi enviado

        sleep_time: tempo entre requisições ao Servidor em segundos

        timeout: tempo total para aguardar resposta, em segundos

    """
    enter_time = time.time()
    rv = None
    try:
        while True:
            time.sleep(sleep_time)
            if time.time() - enter_time >= timeout:
                print('Timeout ao esperar resultado de processamento ' +
                      'Funcao: espera_resposta' +
                      ' Arquivo: ' + bson_file)
                return False
            rv = requests.get(api_url)
            if rv and rv.status_code == 200:
                try:
                    response_json = rv.json()
                    state = response_json.get('state')
                    if state and state in states.SUCCESS:
                        os.remove(bson_file)
                        print('Arquivo ' + bson_file + ' removido.')
                        return True
                    if state and state in states.FAILURE:
                        print(rv.text)
                        return False
                except json.decoder.JSONDecodeError as err:
                    print(err, exc_info=True)
                    print(rv.text)
                    return False

    except Exception as err:
        print(err)
    return False


if __name__ == '__main__':
    print(despacha_dir())
