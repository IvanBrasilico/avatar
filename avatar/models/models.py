import os
from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext import baked
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

Base = declarative_base()


class MySession():
    """Sessão com BD.

    Para definir a sessão com o BD na aplicação. Para os
    testes, passando o parâmetro test=True, um BD na memória
    """

    def __init__(self, arquivo='avatar.db'):
        """Inicializa.
        Params:
            arquivo: Nome do arquivo que contém a base. Passar None
            cria banco de dados na memória
        """
        if arquivo is None:
            path = ':memory:'
        else:
            path = os.path.join(os.getcwd(), arquivo)
            print('***Banco de Dados...', path)
            if os.name != 'nt':
                path = '/' + path
        self._engine = create_engine('sqlite:///' + path, convert_unicode=True)
        Session = sessionmaker(bind=self._engine)
        if arquivo is None:
            self._session = Session()
            Base.metadata.create_all(self.engine)
        else:
            self._session = scoped_session(Session)
            Base.metadata.bind = self._engine
            if not os.path.exists(arquivo):
                Base.metadata.create_all(self._engine)
        self.baked = baked

    @property
    def session(self):
        """Session."""
        return self._session

    @property
    def engine(self):
        """Engine."""
        return self._engine


class FonteImagem(Base):
    """Recintos ou outro fornecedor de imagens de escaneamento."""
    __tablename__ = 'fontesimagem'
    id = Column(Integer, primary_key=True)
    nome = Column(String(20), unique=True)
    caminho = Column(String(200), unique=True)
    pub_date = Column(DateTime)
    imagens = relationship('ConteinerEscaneado', back_populates='fonte')
    agendamento = relationship('Agendamento', back_populates='fonte',
                               uselist=False)

    def __init__(self, nome: str, caminho: str):
        self.nome = nome
        self.caminho = caminho

    def __str__(self):
        return f'{self.nome}, {self.caminho}'

    def total_imagens(self, session):
        return session.query(ConteinerEscaneado).filter(
            ConteinerEscaneado.fonte_id == self.id).count()

    def proximo_agendamento(self, session):
        return session.query(Agendamento).filter(
            Agendamento.fonte_id == self.id,
            Agendamento.proximocarregamento < datetime.now()
        ).first()

    @classmethod
    def cria_ou_edita(cls, session, nome: str, caminho: str,
                      pub_date: DateTime = None):
        """Retorna fonte de nome 'nome' se existente ou nova se não existe."""
        fonte = session.query(FonteImagem).filter(
            FonteImagem.nome == nome).first()
        if fonte is None:  # Cria novo
            fonte = FonteImagem(nome, caminho)
            if pub_date is None:  # default now()
                pub_date = datetime.now()
            fonte.pub_date = pub_date
        else:  # Edita existente
            fonte.caminho = caminho
            if pub_date:  # Só edita se passar valor explícito
                fonte.pub_date = pub_date
        session.add(fonte)
        try:
            session.commit()
            return fonte, f'Gravado: {str(fonte)}'
        except IntegrityError as err:
            session.rollback()
            return None, str(err)

    def exclui(self, session):
        if len(self.imagens) > 0:
            raise Exception('Fonte com importações de imagens já realizadas.'
                            'Não posso excluir.')
        session.delete(self)
        try:
            session.commit()
        except Exception as err:
            self.session.rollback()
            raise err


class ConteinerEscaneado(Base):
    __tablename__ = 'conteineresescaneados'
    id = Column(Integer, primary_key=True)
    fonte_id = Column(Integer, ForeignKey('fontesimagem.id'))
    fonte = relationship('FonteImagem', back_populates='imagens')
    numero = Column(String(11))
    pub_date = Column(DateTime)  # 'Data escaneamento informado do arquivo XML
    file_mdate = Column(DateTime)  # 'Data da última modificação do arquivo')
    file_cdate = Column(DateTime)  # 'Data da criação do arquivo (Windows)')
    origem = Column(String(200)) # Caminho da imagem original
    arqimagemoriginal = Column(String(50)) # Arquivo copiado
    truckid = Column(String(50))
    alerta = Column(Integer)
    exportado = Column(Integer)

    def __init__(self, numero: str, fonte: FonteImagem):
        self.numero = numero
        self.fonte = fonte

    def __str__(self):
        return self.fonte.nome + ' - ' + self.numero + self.pub_date


class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True)
    fonte_id = Column(Integer, ForeignKey('fontesimagem.id'))
    fonte = relationship('FonteImagem', back_populates='agendamento')
    mascarafiltro = Column(String(20))
    # 'Mascara no formato " % Y % m % d" mais qualquer literal', max_length=20)
    diaspararepetir = Column(Integer)
    proximocarregamento = Column(DateTime)  # 'Data do próximo agendamento')

    def __init__(self, mascarafiltro: str, fonte: FonteImagem,
                 data: datetime, diaspararepetir: int = 1):
        self.mascarafiltro = mascarafiltro
        self.fonte = fonte
        self.proximocarregamento = data
        self.diaspararepetir = diaspararepetir

    def processamascara(self):
        return self.proximocarregamento.strftime(self.mascarafiltro)

    def set_proximocarregamento(self, data):
        try:
            self.proximocarregamento = datetime.strptime(data,
                                                         '%Y-%m-%d %H:%M')
        except ValueError:
            raise ValueError(
                data +
                'Formato de data inválido. Formato correto AAAA-MM-DD hh:mm')

    def get_proximocarregamento_fmt(self):
        return self.proximocarregamento.strftime('%Y-%m-%d %H:%M')

    @classmethod
    def agendamentos_pendentes(cls, session):
        return session.query(Agendamento).filter(
            Agendamento.proximocarregamento < datetime.now()
        ).all()

    @classmethod
    def agendamentos_programados(cls, session):
        return session.query(Agendamento).filter(
            Agendamento.proximocarregamento > datetime.now()
        ).all()

    def __str__(self):
        return self.fonte.nome + ' ' + \
            self.proximocarregamento.strftime('%Y-%m-%d %H:%M')
