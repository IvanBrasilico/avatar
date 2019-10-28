import glob
import os
import time
from datetime import datetime

from avatar.utils.utils import lista_jpgs
from avatar.utils.bsonimage import BsonImage, BsonImageList


def monta_lista(pasta):
    """Retorna dicionario com diretorios dentro do caminho e arquivos dentro.

    Nome dos diretórios dentro da pasta é esperado estar no formato:
        "número do contêiner - ocorrência"  (ou, no mínimo, número do contêiner)
        Ex: DFSU2945397 - bagagem com contrafeito

    """
    lista_diretorios = os.listdir(pasta)
    aprocessar = {}
    for diretorio in lista_diretorios:
        infos = diretorio.split('-')
        ocorrencia = ''
        try:
            numero = infos[0].strip()
            if len(infos) > 0:
                ocorrencia = infos[1].strip()
            caminho_atual = os.path.join(pasta, diretorio)
            lista_xmls = glob.glob(caminho_atual, '.xml')
            if len(lista_xmls) > 0:
                caminho_completo_xml = os.path.join(pasta, diretorio, lista_xmls[0])
                lista_imagens = lista_jpgs(caminho_atual)
                caminho_completo_jpeg = os.path.join(pasta, diretorio, lista_imagens[0])
                data_jpg = datetime.fromtimestamp(
                    time.mktime(time.localtime(os.path.getmtime(caminho_completo_jpeg)))
                )
                aprocessar[numero] = (caminho_completo_xml, lista_xmls[0],
                                      caminho_completo_jpeg,
                                      lista_imagens[0], data_jpg, ocorrencia)
        except Exception as err:
            print(err, diretorio)
    return aprocessar


def gera_bson_image_list(caminho, tag):
    aprocessar = monta_lista(caminho)
    bson_image_list = BsonImageList()
    for container, linha in aprocessar.items():
        xmlpath = linha[0]
        filename_xml = linha[1]
        jpgpath = linha[2]
        filename_jpg = linha[3]
        mdate = linha[4]
        ocorrencia = linha[5]
        metadata_jpg = \
            {'contentType': 'image/jpeg',
             'UNIDADE': 'ALFSTS',
             'imagem': jpgpath,
             'dataescaneamento': mdate,
             'criacaoarquivo': mdate,
             'modificacaoarquivo': mdate,
             'numeroinformado': container,
             'ocorrencias': [{'texto': ocorrencia, }],
             'tags': [{'tag': tag, 'usuario': 'ivan'}]
             }
        bson_image_list.addImage(jpgpath, **metadata_jpg)
        metadata_xml = \
            {'contentType': 'text/xml',
             'UNIDADE': 'ALFSTS',
             'imagem': jpgpath,
             'dataescaneamento': mdate,
             'criacaoarquivo': mdate,
             'modificacaoarquivo': mdate,
             'numeroinformado': container
             }
        bson_image_list.addImage(xmlpath, **metadata_xml)
    return bson_image_list
