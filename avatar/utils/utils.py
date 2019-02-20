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
HOMEDIR = os.getcwd()
IMAGES_FOLDER = os.path.join(HOMEDIR, 'images')
BSON_DEST_PATH = os.path.join(HOMEDIR, 'bson')

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
except FileNotFoundError as err:
    logger.error(f'HOMEDIR: {HOMEDIR}')
    logger.error('Arquivo de configuração não encontrado. '
                 'Usando Unidade "ALFSTS".')
    logger.error('Crie arquivo avatar.conf para configurar')
    raise err

tags_numero = ['ContainerId', 'container_no', 'ContainerID1']
tags_data = ['Date', 'SCANTIME', 'ScanTime']


def get_numero_data(root):
    numero = None
    data = None
    for atag in tags_numero:
        for tag in root.iter(atag):
            lnumero = tag.text
            if lnumero is not None:
                logger.debug(f'carregaarquivos - numero-{lnumero}')
                numero = lnumero.replace('?', 'X')
                break

    for atag in tags_data:
        for tag in root.iter(atag):
            data = tag.text
            if data is not None:
                break

    return numero, data


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
        except FileNotFoundError as err:
            logger.warning(err)
            mensagem = mensagem + path_origem + str(err)
            return mensagem, False
        except Exception as err:
            logger.error(err)
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
                    if 'ocr.xml' in f:
                        continue
                    logger.debug(f'carregaarquivos - f = {f}')
                    logger.debug(f'carregaarquivos - dir path = {dirpath}')
                    try:
                        tree = ET.parse(os.path.join(dirpath, f))
                        root = tree.getroot()
                    except ParseError as err:
                        erro = True
                        mensagem = \
                            mensagem + os.path.join(dirpath, f) + \
                            ' XML inválido. ' + str(err) + '\n'
                        continue
                    numero, data = get_numero_data(root)
                    if numero is None or data is None:
                        mensagem = \
                            mensagem + os.path.join(dirpath, f) + \
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
                    lista_jpg = []
                    extensoes = ['*mp.jpg', '*thumbxray.jpg', '*icon.jpg']
                    for extensao in extensoes:
                        lista_jpg = glob.glob(os.path.join(dirpath, extensao))
                        if len(lista_jpg) > 0:
                            break
                    if len(lista_jpg) == 0:
                        erro = True
                        mensagem = mensagem + dirpath + \
                                   ' Imagens (*mp.jpg) não' + \
                                   ' encontradas no caminho.\n'
                        logger.debug('**** numero %s *** data %s' % (numero, data))
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
                        mdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getmtime(file))))
                        cdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getctime(file))))
                        c.file_mdate = mdate
                        c.file_cdate = cdate
                        try:
                            c.pub_date = datetime.strptime(data, '%Y-%m-%d_%H-%M-%S')
                            # datetime(int(ano), int(mes), int(dia))
                        except ValueError as err:
                            c.pub_date = c.file_cdate
                            logger.debug(err)

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


def trata_agendamentos(session, agendamento=None):
    """Consulta agendamentos pendentes e executa carregaarquivos.

    Consulta agendamentos pendentes e executa carregaarquivos,
    passando cada um deles.

    Returns:
        Mensagem de status, erro (True ou False)
    """
    if agendamento is None:
        lista_agendamentos = Agendamento.agendamentos_pendentes(session)
    else:
        lista_agendamentos = [agendamento]
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
                # Se já passou um dia da data de agendamento, atualiza para dia seguinte
                # Senão, continua puxando o mesmo dia.
                if datetime.now() - ag.proximocarregamento > timedelta(days=1):
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
    start = nao_exportados[0].file_cdate
    end = nao_exportados[batch_size - 1].file_cdate
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
    bsonimagelist = BsonImageList()
    for key, value in dict_export.items():
        # Puxa arquivo .jpg
        jpegfile = os.path.join(IMAGES_FOLDER, value['recinto'], value['imagem'])
        caminho = os.path.dirname(jpegfile)
        try:
            bsonimage = BsonImage(filename=jpegfile, **value)
            bsonimagelist.addBsonImage(bsonimage)
        except FileNotFoundError as err:
            logger.error(f'EXPORTA BSON-ERRO:{str(err)}')
            logger.error(f'EXPORTA BSON-Ao exportar: {value["imagem"]}')
        # Puxa arquivo .xml
        try:
            xmlfile = ''
            lista_arquivos = os.listdir(caminho)
            for arquivo in lista_arquivos:
                if arquivo[-4:].lower() == '.xml':
                    xmlfile = arquivo
                    break
            xmlfile = os.path.join(caminho, xmlfile)
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
    try:
        if not os.path.exists(BSON_DEST_PATH):
            os.mkdir(BSON_DEST_PATH)
        bson_file_name = os.path.join(BSON_DEST_PATH, name + '_list.bson')
        while os.path.exists(bson_file_name):  # Nome de arquivo coincidiu!!!
            bson_file_name = bson_file_name + 'E-'
        bsonimagelist.tofile(bson_file_name)
        session.commit()
        s4 = time.time()
        logger.info(f'EXPORTA BSON-BD atualizado em {s4 - s3} segundos')
        logger.warning(f'{batch_size} arquivos exportados para {bson_file_name}')
    except Exception as err:
        session.rollback()
        logger.error(err)
    s5 = time.time()
    logger.info(f'EXPORTA BSON-Bson salvo em {s5 - s4} segundos')
    return dict_export, bson_file_name, batch_size
