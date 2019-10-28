

def pega_xml(caminho):
    arquivos = os.listdir(caminho)
    xmls = [arquivo for arquivo in arquivos if arquivo[-4:] == '.xml']
    return xmls


def monta_lista(pasta):
    lista_diretorios = os.listdir(pasta)
    aprocessar = {}
    for diretorio in lista_diretorios:
        infos = diretorio.split('-')
        ocorrencia = ''
        try:
            numero = infos[0].strip()
            ocorrencia = infos[1].strip()
            caminho_atual = os.path.join(pasta, diretorio)
            xmls = pega_xml(caminho_atual)
            if len(xmls) > 0:
                caminho_completo_xml = os.path.join(pasta, diretorio, xmls[0])
                filename_jpg = pega_jpg(caminho_atual, xmls[0])
                caminho_completo_jpeg = os.path.join(pasta, diretorio, filename_jpg)
                data_jpg = datetime.fromtimestamp(
                    time.mktime(time.localtime(os.path.getmtime(caminho_completo_jpeg)))
                )
                aprocessar[numero] = (caminho_completo_xml, xmls[0],
                                      caminho_completo_jpeg,
                                      filename_jpg, data_jpg, ocorrencia)
        except Exception as err:
            print(err, diretorio)
    return aprocessar



def pega_jpg(caminho, xml):
    arquivos = os.listdir(caminho)
    mesmo_nome = [arquivo for arquivo in arquivos if arquivo[-4:] == '.jpg' and arquivo[:-6].find(xml[-4:])]
    menor_nome_jpg = mesmo_nome[0]
    for nome in mesmo_nome[1:]:
        if len(nome) < len(menor_nome_jpg):
            menor_nome_jpg = nome
    return menor_nome_jpg


def grava_bson_image_list(aprocessar, tag):
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