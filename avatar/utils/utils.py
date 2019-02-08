from datetime import datetime, timedelta
import fnmatch
import glob
import os
import time
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from shutil import copyfile
from sqlalchemy.exc import IntegrityError

from avatar.models.models import Agendamento, ConteinerEscaneado
from avatar.utils.bsonimage import BsonImage, BsonImageList
from avatar.utils.logconf import logger

# size = (256, 120)
BSON_BATCH_SIZE = 400
HOMEDIR = os.getcwd()
IMAGES_FOLDER = os.path.join(HOMEDIR, 'images')
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')

UNIDADE_CONF = os.path.join(HOMEDIR, 'unidade.txt')
try:
    with open(UNIDADE_CONF, 'r') as unidade_file:
        UNIDADE = unidade_file.readline()
except FileNotFoundError:
    UNIDADE = 'ALFSTS'
    logger.warning(f'HOMEDIR: {HOMEDIR}')
    logger.warning('Arquivo de configuração não encontrado. '
                   'Usando Unidade "ALFSTS".')
    logger.warning('Crie arquivo unidade.txt para configurar')


def carregaarquivos(agendamento: Agendamento, session):
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
        agendamento: Objeto Agendamento a processar
        session: Conexão com o Banco de Dados
    :return: mensagem: str, erro: bool
    """
    caminho = agendamento.processamascara()
    fonteimagem = agendamento.fonte
    logger.debug(fonteimagem.caminho, caminho)
    path_origem = os.path.join(fonteimagem.caminho, caminho)
    path_destino = os.path.join(IMAGES_FOLDER, fonteimagem.nome)
    logger.debug(f'Origem: {path_origem}')
    mensagem = ''
    erro = False
    try:
        try:
            lista_dir = [dir for dir in os.listdir(path_origem)
                         if os.path.isdir(os.path.join(path_origem, dir))]
        except Exception as err:
            logger.warning(err)
            mensagem = mensagem + path_origem + str(err)
            return mensagem, True
        logger.debug(lista_dir)
        if len(lista_dir) == 0:
            logger.debug(f'LISTA DE DIRETÓRIOS VAZIA: {lista_dir}')
            logger.debug(f'Listagem de arquivos: {os.listdir(path_origem)}')
            logger.debug(f'Caminho: {path_origem}')
            mensagem = mensagem + path_origem + \
                       ' retornou lista vazia!! Sem acesso? \n'
            return mensagem, True
        for result in glob.iglob(path_origem):
            for dirpath, dirnames, files in os.walk(result):
                for f in fnmatch.filter(files, '*.xml'):
                    logger.debug(f'carregaarquivos - f = {f}')
                    logger.debug(f'carregaarquivos - dir path = {dirpath}')
                    try:
                        tree = ET.parse(os.path.join(dirpath, f))
                        root = tree.getroot()
                    except ParseError as err:
                        erro = True
                        mensagem = \
                            mensagem + path_origem + \
                            ' XML inválido. ' + str(err) + '\n'
                        continue

                    numero = None
                    data = None
                    for tag in root.iter('ContainerId'):
                        lnumero = tag.text
                        if lnumero is not None:
                            logger.debug(f'carregaarquivos - numero-{lnumero}')
                            numero = lnumero.replace('?', 'X')
                    for tag in root.iter('Date'):
                        data = tag.text
                    if numero is None or data is None:
                        mensagem = \
                            mensagem + path_origem + \
                            ' XML inválido. ' + \
                            'XML deve conter chaves ContainerId e Date.'
                        continue

                    truckid = 'NI'
                    operador = 'NI'
                    alerta = False
                    for tag in root.iter('TruckId'):
                        truckid = tag.text
                    for tag in root.iter('Login'):
                        operador = tag.text
                    for tag in root:
                        for t in tag.getchildren():
                            if t.text == 'AL':
                                alerta = True
                    ano = data[:4]
                    mes = data[5:7]
                    dia = data[8:10]
                    destparcial = os.path.join(ano, mes, dia, numero)
                    destcompleto = os.path.join(path_destino, destparcial)
                    logger.debug(f'destcompleto {destcompleto}')
                    lista_jpg = glob.glob(os.path.join(dirpath, '*mp.jpg'))
                    if len(lista_jpg) == 0:
                        erro = True
                        mensagem = mensagem + destcompleto + \
                                   ' Imagem não encontrada.\n'
                        continue
                    try:
                        os.makedirs(destcompleto)
                    except FileExistsError as e:
                        mensagem = mensagem + \
                                   destcompleto + ' já existente. - pulando\n'
                        continue
                    copyfile(os.path.join(dirpath, f),
                             os.path.join(destcompleto, f))
                    for file in lista_jpg:
                        name = os.path.basename(file)
                        logger.debug(f'Copiando imagem {name}')
                        copyfile(file, os.path.join(destcompleto, name))
                        c = ConteinerEscaneado(numero, fonteimagem)
                        c.arqimagemoriginal = destparcial + '/' + name
                        c.pub_date = datetime(int(ano), int(mes), int(dia))
                        mdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getmtime(file))))
                        cdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getctime(file))))
                        c.file_mdate = mdate
                        c.file_cdate = cdate
                        logger.debug(f'{c.pub_date}, {c.file_mdate},'
                                     f' {c.file_cdate}')
                        c.truckid = truckid
                        c.alerta = alerta
                        c.operador = operador
                        c.exportado = 0
                        try:
                            session.add(c)
                            session.commit()
                        except IntegrityError:
                            erro = True
                            mensagem = mensagem + destparcial + numero + \
                                       ' já cadastrado?!\n'
    except Exception as err:
        raise (err)
        erro = True
        mensagem = str(err)
    return mensagem, erro


def trata_agendamentos(session):
    """Consulta agendamentos pendentes e executa carregaarquivos.

    Consulta agendamentos pendentes e executa carregaarquivos,
    passando cada um deles.

    Returns:
        Mensagem de status, erro (True ou False)
    """
    lista_agendamentos = Agendamento.agendamentos_pendentes(session)
    if len(lista_agendamentos) > 0:
        logger.info(f'Processando agendamentos encontrados!!!')
        for ag in lista_agendamentos:
            logger.info(ag)
            mensagem, erro = carregaarquivos(ag, session)
            if erro:
                logger.error(mensagem)
            else:
                logger.info(mensagem)
            if not erro:
                ag.proximocarregamento = \
                    ag.proximocarregamento + \
                    timedelta(days=ag.diaspararepetir)
                session.add(ag)
                session.commit()
        return mensagem, erro
    else:
        logger.warning('trata_agendamentos: '
                       'Não foram encontrados agendamentos!!!')
        return 'Não foram encontrados agendamentos.', True


def exporta_bson(session, batch_size: int = BSON_BATCH_SIZE):
    s0 = time.time()
    nao_exportados = session.query(ConteinerEscaneado).filter(
        ConteinerEscaneado.exportado == 0).limit(batch_size).all()
    qtde = len(nao_exportados)
    if batch_size > qtde:  # Não tem arquivos suficientes ainda
        logger.warning(f'Qtde {qtde} < batch_size {batch_size}. '
                       'Abortando exporta_bson.')
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
            'fonte': containerescaneado.fonte.nome,
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
    bsonimagelist = BsonImageList()
    for key, value in dict_export.items():
        # Puxa arquivo .jpg
        jpegfile = os.path.join(IMAGES_FOLDER, value['fonte'], value['imagem'])
        # print(jpegfile)
        try:
            bsonimage = BsonImage(filename=jpegfile, **value)
            bsonimagelist.addBsonImage(bsonimage)
        except FileNotFoundError as err:
            logger.error(f'EXPORTA BSON-ERRO:{str(err)}')
            logger.error(f'EXPORTA BSON-Ao exportar: {value["imagem"]}')
        # Puxa arquivo .xml
        try:
            xmlfile = jpegfile.split('S_stamp')[0] + '.xml'
            value['contentType'] = 'text/xml'
            bsonimage = BsonImage(filename=xmlfile, **value)
            bsonimagelist.addBsonImage(bsonimage)
        except FileNotFoundError as err:
            logger.error(f'EXPORTA BSON-ERRO:{str(err)}')
            logger.error(f'EXPORTA BSON-Ao exportar: {xmlfile}')
    name = datetime.strftime(start, '%Y-%m-%d_%H-%M-%S') + '_' + \
           datetime.strftime(end, '%Y-%m-%d_%H-%M-%S')
    s3 = time.time()
    logger.info(f'EXPORTA BSON-Bson montado em {s3 - s2} segundos')
    for containerescaneado in nao_exportados:
        containerescaneado.exportado = 1
        session.add(containerescaneado)
    session.commit()
    s4 = time.time()
    logger.info(f'EXPORTA BSON-BD atualizado em {s4 - s3} segundos')
    try:
        if not os.path.exists(BSON_DEST_PATH):
            os.mkdir(BSON_DEST_PATH)
        bson_file_name = os.path.join(BSON_DEST_PATH, name + '_list.bson')
        bsonimagelist.tofile(bson_file_name)
        logger.warning(f'{qtde} arquivos exportados para {bson_file_name}')
    except Exception as err:
        session.rollback()
        logger.warning(err)
    s5 = time.time()
    logger.info(f'EXPORTA BSON-Bson salvo em {s5 - s4} segundos')
    return dict_export, bson_file_name, qtde
