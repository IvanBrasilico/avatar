import sys
from datetime import datetime
from logging import DEBUG

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append('.')

from avatar.models.models import Agendamento, FonteImagem, Base
from avatar.utils.utils import trata_agendamentos


def cria_fontes_e_agendamentos(session, engine):
    # Criar todas as tabelas (assumindo que Base está importado do seu modelo)
    Base.metadata.create_all(engine)
    fontes = []
    # Criar fontes conforme seu pedido
    fontes.append(FonteImagem(nome='BTP1', caminho='./tests/pastas_exemplo/btp1'))
    fontes.append(FonteImagem(nome='BTP2', caminho='./tests/pastas_exemplo/btp2'))
    fontes.append(FonteImagem(nome='BTP3', caminho='./tests/pastas_exemplo/btp3'))
    session.add_all(fontes)
    session.commit()

    agendamentos = []
    for fonte in fontes:
        # Criar agendamentos para essas fontes, com próxima data para já (pendente)
        agendamentos.append(Agendamento(
            mascarafiltro='%Y%m/%Y%m%d',
            fonte=fonte,
            data=datetime(2025, 11, 14),  # já pendente
            diaspararepetir=1
        ))
    session.add_all(agendamentos)
    session.commit()


if __name__ == '__main__':
    from avatar.utils.logconf import logger

    logger.setLevel(DEBUG)
    # Criar engine e sessão para teste em memória
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    cria_fontes_e_agendamentos(session, engine)
    # Testar a função trata_agendamentos
    mensagem, erro = trata_agendamentos(session)
    print('Mensagem:', mensagem)
    print('Erro:', erro)
