import fnmatch
import glob
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from shutil import copyfile
from xml.etree.ElementTree import ParseError

from sqlalchemy.exc import IntegrityError

from avatar.models.models import Agendamento, ConteinerEscaneado
from avatar.utils.bsonimage import BsonImage, BsonImageList
from avatar.utils.conf import BSON_BATCH_SIZE, BSON_DEST_PATH, EXTENSOES_JPG, \
    IMAGES_FOLDER, TAGS_DATA, TAGS_NUMERO, UNIDADE
from avatar.utils.logconf import logger


def get_numero_data(root):
    numero = None
    data = None
    for atag in TAGS_NUMERO:
        for tag in root.iter(atag):
            lnumero = tag.text
            if lnumero is not None:
                logger.debug(f'carregaarquivos - numero-{lnumero}')
                numero = lnumero.replace('?', 'X')
                break
    for atag in TAGS_DATA:
        for tag in root.iter(atag):
            data = tag.text
            if data is not None:
                break
    return numero, data


def get_lista_jpgs(destcompleto, dirpath, mensagem):
    """Função auxiliar de carrega_arquivos"""
    for extensao in EXTENSOES_JPG:
        lista_jpg = glob.glob(os.path.join(dirpath, extensao))
        if len(lista_jpg) > 0:
            break
    if len(lista_jpg) == 0:
        mensagem = mensagem + dirpath + \
                   ' Imagens %s não' % EXTENSOES_JPG + \
                   ' encontradas no caminho.\n'
        logger.debug('**** destcompleto %s *** ' % destcompleto)
        return lista_jpg, [], mensagem
    try:
        os.makedirs(destcompleto)
    except FileExistsError:
        pass
    # TODO: comparar arquivos, caso cdate ou MD5 sejam
    # diferente, copiar com nome modificado!!!!
    lista_jpg_origem = []
    lista_jpg_destino = []
    for origem in lista_jpg:
        filename = os.path.basename(origem)
        destino = os.path.join(destcompleto, filename)
        if os.path.exists(destino):
            cdate_origem = os.path.getctime(origem)
            cdate_destino = os.path.getctime(destino)
            # Se arquivo existente, pula...
            if cdate_destino == cdate_origem:
                mensagem = mensagem + \
                           destino + ' já existente. - pulando\n'
                continue
            else:  # Se existente mas com data diferente, copia com outro nome
                destino = destino + \
                          datetime.strftime(datetime.now(), 'Y%m%d%H%M')
        lista_jpg_origem.append(origem)
        lista_jpg_destino.append(destino)

    return lista_jpg_origem, lista_jpg_destino, mensagem


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
                    lista_origem, lista_destino, mensagem = \
                        get_lista_jpgs(destcompleto, dirpath, mensagem)
                    # Copia XML
                    if len(lista_origem) == 0:
                        continue
                    try:
                        copyfile(os.path.join(dirpath, f),
                                 os.path.join(destcompleto, f))
                    except FileExistsError:
                        pass
                    # Copia jpgs
                    for origem, destino in zip(lista_origem, lista_destino):
                        logger.debug(f'Copiando {origem} para {destino}')
                        copyfile(origem, destino)
                        c = ConteinerEscaneado(numero, fonteimagem)
                        c.arqimagemoriginal = destino
                        mdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getmtime(origem))))
                        cdate = datetime.fromtimestamp(time.mktime(
                            time.localtime(os.path.getctime(origem))))
                        c.file_mdate = mdate
                        c.file_cdate = cdate
                        try:
                            c.pub_date = datetime.strptime(data,
                                                           '%Y-%m-%d_%H-%M-%S')
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
                        except IntegrityError as err:
                            erro = True
                            mensagem = mensagem + \
                                       f'{err}!! {numero} já cadastrado?!\n'
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
                # Se já passou um dia da data de agendamento,
                # atualiza para dia seguinte
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
        jpegfile = os.path.join(IMAGES_FOLDER, value['recinto'],
                                value['imagem'])
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
        logger.info(
            f'EXPORTA BSON-BD atualizado em {s4 - s3} segundos')
        logger.warning(
            f'{batch_size} arquivos exportados para {bson_file_name}')
    except Exception as err:
        session.rollback()
        logger.error(err)
    s5 = time.time()
    logger.info(f'EXPORTA BSON-Bson salvo em {s5 - s4} segundos')
    return dict_export, bson_file_name, batch_size
