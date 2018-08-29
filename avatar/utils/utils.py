import datetime
import fnmatch
import glob
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from shutil import copyfile
from sqlalchemy.exc import IntegrityError

from avatar.models.models import Agendamento, ConteinerEscaneado, FonteImagem
from avatar.utils.bsonimage import BsonImage, BsonImageList
from avatar.utils.logconf import logger

# size = (256, 120)
HOMEDIR = os.path.dirname(os.path.abspath(__file__))
UNIDADE_CONF = os.path.join(HOMEDIR, 'unidade.txt')
BSON_BATCH_SIZE = 1000
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')
try:
    with open(UNIDADE_CONF, 'r') as unidade_file:
        UNIDADE = unidade_file.readline()
except FileNotFoundError:
    UNIDADE = 'ALFSTS'
    logger.warning('Arquivo de configuração não encontrado. '
                   'Usando Unidade "ALFSTS".')
    logger.warning('Crie arquivo unidade.txt para configurar')


def carregaarquivos(caminho: str, fonteimagem: FonteImagem):
    """Copia arquivos do caminho na Fonte.

    (LAÇO) Verifica se há arquivos XML no sub-diretório da FonteImagem.
        CASO existam, copia um a um para o diretório destino padrão (local).
        (SE) ANTES de copiar XML, lê número do contêiner do XML tenta criar
            diretório Ano/Mes/Dia/Numero. Caso já exista, considera cópia
            feita, grava mensagem no log e parte para o próximo XML da lista.
        (SENÃO) Não existindo o diretório destino,
            CRIA diretório
            COPIA XML
            COPIA arquivo com final 'mp.jpg' do mesmo diretório do XML
            CRIA registro para ConteinerEscaneado relativo a esta cópia

    Params:
        caminho: sub-diretório a copiar
        fonteimagem: FonteImagem
    :return: mensagem: str, erro: bool
    """
    path_origem = os.path.join(fonteimagem.caminho, caminho)
    path_destino = os.path.join(HOMEDIR, 'images')
    logger.debug(f'Origem: {path_origem}')
    numero = None
    mensagem = ''
    erro = False
    alerta = False
    try:
        for result in glob.iglob(path_origem):
            for dirpath, dirnames, files in os.walk(result):
                for f in fnmatch.filter(files, '*.xml'):
                    logger.debug(f'carregaarquivos - f{f}')
                    logger.debug(f'carregaarquivos - dir path{dirpath}')
                    tree = ET.parse(os.path.join(dirpath, f))
                    root = tree.getroot()
                    for tag in root.iter('ContainerId'):
                        lnumero = tag.text
                        if lnumero is not None:
                            logger.debug(f'carregaarquivos - numero-{lnumero}')
                            numero = lnumero.replace('?', 'X')
                    for tag in root.iter('TruckId'):
                        truckid = tag.text
                    for tag in root.iter('Date'):
                        data = tag.text
                    for tag in root.iter('Login'):
                        operador = tag.text
                    for tag in root:
                        for t in tag.getchildren():
                            if t.text == 'AL':
                                alerta = True
                    if numero is not None:
                        logger.debug('Processando...')
                        ano = data[:4]
                        mes = data[5:7]
                        dia = data[8:10]
                        destparcial = os.path.join(ano, mes, dia, numero)
                        destcompleto = os.path.join(path_destino, destparcial)
                        logger.debug(f'destcompleto {destcompleto}')
                        logger.debug(f'destparcial {destparcial}')
                        try:
                            os.makedirs(destcompleto)
                        except FileExistsError as e:
                            erro = True
                            mensagem = mensagem + \
                                       destcompleto + ' já existente.\n'
                            logger.debug(f'{destcompleto} já existente')
                            continue
                        copyfile(os.path.join(dirpath, f), os.path.join(destcompleto, f))
                        for file in glob.glob(os.path.join(dirpath, '*mp.jpg')):
                            name = os.path.basename(file)
                            logger.debug(f'Copiango imagem {name}')
                            copyfile(file, os.path.join(destcompleto, name))
                            c = ConteinerEscaneado()
                            c.numero = numero
                            c.arqimagemoriginal = destparcial + '/' + name
                            c.fonte = fonteimagem
                            c.pub_date = data
                            mdate = time.localtime(os.path.getmtime(file))
                            mdate = time.strftime('%Y-%m-%d %H:%M:%S%z', mdate)
                            cdate = time.localtime(os.path.getctime(file))
                            cdate = time.strftime('%Y-%m-%d %H:%M:%S%z', cdate)
                            c.file_mdate = mdate
                            c.file_cdate = cdate
                            logger.debug(f'{c.pub_date}, {c.file_mdate}, {c.file_cdate}')
                            c.truckid = truckid
                            c.alerta = alerta
                            c.operador = operador
                            c.exportado = 0
                            try:
                                c.save()
                            except IntegrityError:
                                erro = True
                                mensagem = mensagem + destparcial + numero + ' já cadastrado?!\n'
                        numero = None
        else:
            mensagem = mensagem + path_origem + ' retornou lista vazia!! Sem acesso? \n'
            erro = True
    except Exception as err:
        raise (err)
        erro = True
        mensagem = str(err)
    return mensagem, erro


def trata_agendamentos():
    lista_agendamentos = Agendamento.agendamentos_pendentes()
    if len(lista_agendamentos) > 0:
        logger.warning(f'Processando agendamentos encontrados!!!')
        for ag in lista_agendamentos:
            logger.info(ag)
            fonte = ag.fonte
            caminho = ag.processamascara()
            mensagem, erro = carregaarquivos(caminho, fonte)
            logger.info(mensagem)
            if not erro:
                ag.proximocarregamento = ag.proximocarregamento + \
                                         datetime.timedelta(days=ag.diaspararepetir)
                ag.save()
    else:
        logger.warning('Não foram encontrados agendamentos!!!')


def exporta_bson(batch_size=BSON_BATCH_SIZE):
    s0 = time.time()
    nao_exportados = ConteinerEscaneado.objects.all().filter(
        exportado=0)[:batch_size]
    qtde = len(nao_exportados)
    if batch_size > qtde:  # Não tem arquivos suficientes ainda
        return {}, '', qtde
    dict_export = {}
    start = nao_exportados[0].pub_date
    end = nao_exportados[batch_size - 1].pub_date
    s1 = time.time()
    logger.info(f'EXPORTA BSON-Consulta no banco durou {s1 - s0}segundos')
    for containerescaneado in nao_exportados:
        # print(containerescaneado.numero)
        imagem = os.path.join(
            *containerescaneado.arqimagemoriginal.split('\\'))
        dict_export[str(containerescaneado.id)] = {
            'contentType': 'image/jpeg',
            'id': UNIDADE + str(containerescaneado.id),
            'UNIDADE': UNIDADE,
            'idcov': str(containerescaneado.id),
            'imagem': imagem,
            'dataescaneamento': containerescaneado.pub_date,
            'criacaoarquivo': containerescaneado.file_cdate,
            'modificacaoarquivo': containerescaneado.file_mdate,
            'numeroinformado': containerescaneado.numero,
            'truckid': containerescaneado.truckid,
            'recintoid': str(containerescaneado.fonte.id),
            'recinto': containerescaneado.fonte.nome
        }
    s2 = time.time()
    logger.info(f'EXPORTA BSON-Dicionário montado em {s2 - s1} segundos')
    with open('log' + datetime.datetime.now().strftime('%Y%m%d'), 'a') as f:
        bsonimagelist = BsonImageList()
        for key, value in dict_export.items():
            # Puxa arquivo .jpg
            jpegfile = os.path.join(IMG_FOLDER, value['imagem'])
            # print(jpegfile)
            try:
                bsonimage = BsonImage(filename=jpegfile, **value)
                bsonimagelist.addBsonImage(bsonimage)
            except FileNotFoundError as err:
                f.write(str(err) + '\n')
                logger.error(f'EXPORTA BSON-ERRO:{str(err)}')
                logger.error(f'EXPORTA BSON-Ao exportar: {value["imagem"]}')
            # Puxa arquivo .xml
            try:
                xmlfile = jpegfile.split('S_stamp')[0] + '.xml'
                value['contentType'] = 'text/xml'
                bsonimage = BsonImage(filename=xmlfile, **value)
                bsonimagelist.addBsonImage(bsonimage)
            except FileNotFoundError as err:
                f.write(str(err) + '\n')
                logger.error(f'EXPORTA BSON-ERRO:{str(err)}')
                logger.error(f'EXPORTA BSON-Ao exportar: {xmlfile}')
        f.close()
    name = datetime.datetime.strftime(start, '%Y-%m-%d_%H-%M-%S') + '_' + \
           datetime.datetime.strftime(end, '%Y-%m-%d_%H-%M-%S')
    s3 = time.time()
    logger.info(f'EXPORTA BSON-Bson montado em {s3 - s2} segundos')
    for containerescaneado in nao_exportados:
        containerescaneado.exportado = 1
        containerescaneado.save()
    s4 = time.time()
    logger.info(f'EXPORTA BSON-BD atualizado em {s4 - s3} segundos')
    bsonimagelist.tofile(os.path.join(DEST_PATH, name + '_list.bson'))
    s5 = time.time()
    logger.info(f'EXPORTA BSON-Bson salvo em {s5 - s4} segundos')
    return dict_export, name, qtde
