import os
import datetime
import time
# from .filefunctions import carregaarquivos
# from .bsonimage import BsonImage, BsonImageList
from sys import platform

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker


class MySession():
    """Sessão com BD.

    Para definir a sessão com o BD na aplicação. Para os
    testes, passando o parâmetro test=True, um BD na memória
    """

    def __init__(self, base, arquivo='avatar.db'):
        """Inicializa.
        Params:
            base: driver de banco de dados
            arquivo: Nome do arquivo que contém a base. Passar None
            cria banco de dados na memória
        """
        if arquivo is None:
            path = ':memory:'
        else:
            path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), arquivo)
            print('***Banco de Dados...', path)
            if os.name != 'nt':
                path = '/' + path
        self._engine = create_engine('sqlite:///' + path, convert_unicode=True)
        Session = sessionmaker(bind=self._engine)
        if arquivo is None:
            self._session = Session()
        else:
            self._session = scoped_session(Session)
            base.metadata.bind = self._engine

    @property
    def session(self):
        """Session."""
        return self._session

    @property
    def engine(self):
        """Engine."""
        return self._engine


Base = declarative_base()

association_table = Table('basesorigem_padroesrisco', Base.metadata,
                          Column('left_id', Integer,
                                 ForeignKey('basesorigem.id')),
                          Column('right_id', Integer,
                                 ForeignKey('padroesrisco.id'))
                          )



class FonteImagem(Base):
    """Recintos ou outro fornecedor de imagens de escaneamento."""
    __tablename__ = 'fontesimagem'
    id = Column(Integer, primary_key=True)
    nome = Column(String(20), unique=True)
    caminho = Column(String(200), unique=True)
    pub_date = Column(DateTime)
    imagens = relationship('ConteinerEscaneado', back_populates='fonte')

    def __str__(self):
        return self.nome


class ConteinerEscaneado(Base):
    __tablename__ = 'conteineresescaneados'
    id = Column(Integer, primary_key=True)
    fonte_id = Column(Integer)
    fonte = relationship('FonteImagem', back_populates='imagens')
    numero = Column(String(11))
    pub_date = Column(DateTime) # 'Data do escaneamento retirada do arquivo XML')
    file_mdate = Column(DateTime) #'Data da última modificação do arquivo')
    file_cdate = Column(DateTime) #'Data da criação do arquivo (Windows)')
    arqimagemoriginal = Column(String(50))
    arqimagem = Column(String(50))
    exportado = Column(Integer)

    """
    def getTotal(self):
        return ConteinerEscaneado.objects.count()

    def getTotalporFonteImagem(self):
        return ConteinerEscaneado.objects.values('fonte').annotate(fcount=models.Count('fonte'))
    """

class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True)
    fonte_id = Column(Integer)
    fonte = relationship('FonteImagem', back_populates='imagens')
    mascarafiltro = Column(String(20))
    # 'Mascara no formato " % Y % m % d" mais qualquer literal', max_length=20)
    diaspararepetir = Column(Integer)
    proximocarregamento = Column(DateTime) #'Data do próximo agendamento')

    def processamascara(self):
        return self.proximocarregamento.strftime(self.mascarafiltro)

    def agendamentos_pendentes(self):
        return Agendamento.objects.all().filter(proximocarregamento__lt=datetime.datetime.now())

    def agendamentos_programados(self):
        return Agendamento.objects.all().filter(proximocarregamento__gt=datetime.datetime.now())

    def __str__(self):
        return self.fonte.nome+' '+self.proximocarregamento.strftime('%Y%m%d %H%M')


def trata_agendamentos():
    lista_agendamentos = Agendamento.agendamentos_pendentes()
    if len(lista_agendamentos) > 0:
        print('Tem agendamentos!')
        from .views import homedir, size
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


IMG_FOLDER = os.path.join(os.path.dirname(
    __file__), 'static', 'busca')
DEST_PATH = os.path.join(os.path.dirname(__file__))
UNIDADE = 'ALFSTS:'
BATCH_SIZE = 1000

# Uncomment if images are outside (on development station for example)
# Automatically assumes that if running on linux is on development station,
# Since this module normally run in windows stations to acquire files
# """
if platform != 'win32':
    print('Tks, Lord!!! No weird windows...')
    IMG_FOLDER = os.path.join(os.path.dirname(
        __file__), '..', '..', '..', 'imagens')
    DEST_PATH = os.path.join(os.path.dirname(
        __file__), '..', '..', '..', 'files', 'BSON')
# """


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
