import datetime
from avatar.models.models import Agendamento

from ajna_commons import BsonImage, BsonImageList
from .views import homedir, size
from PIL import Image
import os
import glob
# from scipy import misc
import xml.etree.ElementTree as ET
import fnmatch
from shutil import copyfile
import time
from datetime import datetime


def carregaarquivos(homedir, caminho, size, fonteimagem):
    path = os.path.join(fonteimagem.caminho, caminho)
    pathdest = os.path.join(homedir, 'static', 'busca')
    print('path', path)
    numero = None
    mensagem = ''
    erro = False
    alerta = False
    from .models import ConteinerEscaneado
    try:
        for result in glob.iglob(path):
            for dirpath, dirnames, files in os.walk(result):
                for f in fnmatch.filter(files, '*.xml'):
                    print('carregaarquivos - f', f)
                    print('carregaarquivos - dir path', dirpath)
                    tree = ET.parse(os.path.join(dirpath, f))
                    root = tree.getroot()
                    for tag in root.iter('ContainerId'):
                        lnumero = tag.text
                        if lnumero is not None:
                            print("Numero")
                            print(lnumero)
                            numero = lnumero.replace('?', 'X')
                    for tag in root.iter('TruckId'):
                        truckid=tag.text
                    for tag in root.iter('Date'):
                        data=tag.text
                    for tag in root.iter('Login'):
                        operador=tag.text
                    for tag in root:
                        for t in tag.getchildren():
                            if t.text == 'AL':
                                alerta = True
                    if numero is not None:
                        print('Processando...')
                        ano = data[:4]
                        mes = data[5:7]
                        dia = data[8:10]
                        destparcial = os.path.join(ano, mes, dia, numero)
                        destcompleto = os.path.join(pathdest, destparcial)
                        print('destcompleto', destcompleto)
                        print('destparcial', destparcial)
                        try:
                            os.makedirs(destcompleto)
                        except FileExistsError as e:
                            erro = True
                            mensagem = mensagem + \
                            destcompleto + ' já existente.\n'
                            print(destcompleto, 'já existente')
                            continue
                        copyfile(os.path.join(dirpath, f), os.path.join(destcompleto, f))
                        for file in glob.glob(os.path.join(dirpath,'*mp.jpg')):
                            name = os.path.basename(file)
                            print(name)
                            copyfile(file, os.path.join(destcompleto, name))
                            # recortaesalva(file, size, os.path.join(destcompleto, numero+'.jpg'))
                            c = ConteinerEscaneado()
                            c.numero = numero
                            # c.arqimagem = destparcial+'/'+numero+'.jpg'
                            c.arqimagemoriginal = destparcial+'/'+name
                            c.fonte = fonteimagem
                            c.pub_date = data
                            mdate = time.localtime(os.path.getmtime(file))
                            mdate = time.strftime('%Y-%m-%d %H:%M:%S%z', mdate)
                            cdate = time.localtime(os.path.getctime(file))
                            cdate = time.strftime('%Y-%m-%d %H:%M:%S%z', cdate)
                            c.file_mdate = mdate
                            c.file_cdate = cdate #time.localtime(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')
                            print(c.pub_date, c.file_mdate, c.file_cdate)
                            c.truckid = truckid
                            c.alerta = alerta
                            c.operador = operador
                            c.exportado = 0
                            try:
                                c.save()
                                # mensagem = mensagem + numero + " incluído"
                            except IntegrityError as e:
                                erro = True
                                mensagem = mensagem + path + numero + ' já cadastrado?!\n'
                        numero = None
        else:
            mensagem = mensagem + path + ' retornou lista vazia!! Sem acesso? \n'
            erro = True
    except Exception as err:
        raise(err)
        erro = True
        mensagem = str(err)
    return mensagem, erro

def trata_agendamentos():
    lista_agendamentos = Agendamento.agendamentos_pendentes()
    if len(lista_agendamentos) > 0:
        print('Tem agendamentos!')
        with open('log' + datetime.datetime.now().strftime('%Y%m%d'), 'a') as f:
            for ag in lista_agendamentos:
                fonte = ag.fonte
                caminho = ag.processamascara()
                mensagem, erro = carregaarquivos(homedir, caminho, size, fonte)
                f.write(mensagem+'\n')
                if not erro:
                    ag.proximocarregamento = ag.proximocarregamento + \
                        datetime.timedelta(days=ag.diaspararepetir)
                    ag.save()
            f.close()
    else:
        print('Não tem agendamentos!')

def exporta_bson(batch_size=BATCH_SIZE):
    if not batch_size:
        batch_size = BATCH_SIZE
    s0 = time.time()
    nao_exportados = ConteinerEscaneado.objects.all().filter(
        exportado=0)[:batch_size]
    qtde = len(nao_exportados)
    if batch_size > qtde: #  Não tem arquivos suficientes ainda
        return {}, '', qtde
    dict_export = {}
    start = nao_exportados[0].pub_date
    end = nao_exportados[batch_size - 1].pub_date
    s1 = time.time()
    print('Consulta no banco efetuada em ', s1 - s0, ' segundos')
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
    print('Dicionário montado em ', s2 - s1, ' segundos')
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
                f.write(str(err)+'\n')
                print(str(err))
                print(value['imagem'])

            # Puxa arquivo .xml
            try:
                xmlfile = jpegfile.split('S_stamp')[0] + '.xml'
                value['contentType'] = 'text/xml'
                bsonimage = BsonImage(filename=xmlfile, **value)
                bsonimagelist.addBsonImage(bsonimage)
            except FileNotFoundError as err:
                f.write(str(err)+'\n')
                print(str(err))
                print(value['imagem'])
        f.close()
    name = datetime.datetime.strftime(start, '%Y-%m-%d_%H-%M-%S') + '_' + \
        datetime.datetime.strftime(end, '%Y-%m-%d_%H-%M-%S')
    s3 = time.time()
    print('Bson montado em ', s3 - s2, ' segundos')
    for containerescaneado in nao_exportados:
        containerescaneado.exportado = 1
        containerescaneado.save()
    s4 = time.time()
    print('Banco de dados atualizado em ', s4 - s3, ' segundos')
    bsonimagelist.tofile(os.path.join(DEST_PATH, name + '_list.bson'))
    s5 = time.time()
    print('Bson salvo em ', s5 - s4, ' segundos')
    return dict_export, name, qtde