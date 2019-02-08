"""Script de linha de comando para uso do Avatar."""
import click
import time
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from avatar.models.models import Agendamento, FonteImagem, MySession
from avatar.utils.utils import (carregaarquivos, exporta_bson,
                                trata_agendamentos)
from avatar.utils.logconf import console, logger
from logging import DEBUG

mysession = MySession()
session = mysession.session


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.obj = debug
    if debug:
        print('Ativando DEBUG')
        console.setLevel(DEBUG)
        logger.setLevel(DEBUG)
        logger.debug('DEBUG ativado')


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.option('--caminho', prompt=True,
              help='Caminho Local para acesso'
                   'às imagens (Unidade de disco e pasta)')
@click.pass_obj
def add(ctx, nome, caminho):
    """Adiciona fonte de imagem (edita se já existir).
        Params:
            nome - Nome da Fonte
            caminho - Caminho Local para acesso às imagens
             (Unidade de disco e pasta)
    """
    fonte, mensagem = FonteImagem.cria_ou_edita(session, nome, caminho)
    print(mensagem)


@cli.command()
@click.pass_obj
def lista(ctx):
    """Lista fontes de imagem cadastradas."""
    print('Fonte, Caminho')
    fontes = session.query(FonteImagem).all()
    for fonte in fontes:
        print(fonte)


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.pass_obj
def remove(ctx, nome):
    """Remove fonte de imagem.
        Params:
            nome - Nome da Fonte
    """
    excluido = session.query(FonteImagem).filter(
        FonteImagem.nome == nome).delete()
    session.commit()
    if excluido > 0:
        print(f'FonteImagem {nome} excluída')
    else:
        print(f'FonteImagem {nome} não encontrada')


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.option('--data', prompt=True, help='Data a copiar format AAAA-mm-dd')
@click.pass_obj
def copia(ctx, nome, data):
    """Copia imagens se disponíveis.
        Params:
            nome - Nome da Fonte
            data - Dia a copiar imagens
    """
    try:
        fonte = session.query(FonteImagem).filter(
            FonteImagem.nome == nome).one()
        try:
            proximocarregamento = datetime.strptime(data, '%Y-%m-%d')
        except ValueError:
            print('Formato de data inválido. Formato correto AAAA-MM-DD.')
            return
        agendamento = Agendamento('%Y\%m\%d', fonte, proximocarregamento)
        print(f'Iniciando cópia de arquivos da Fonte de Imagens {nome}'
              f' a partir de {data}')
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, session)
        if erro:
            logger.warning(mensagem)
        else:
            logger.info(mensagem)
    except NoResultFound as err:
        print(f'Fonte "{nome}" não encontrada')


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.option('--data', prompt=True, help='Data a copiar')
@click.option('--mascara', default='%Y\%m\%d',
              help='Máscara (%Y/%m/%d) do caminho')
@click.pass_obj
def agendar(ctx, nome, data, mascara):
    """Cria um agendamento de cópia de imagens.
        Params:
            nome - Nome da Fonte
            data - Dia a copiar imagens
    """
    try:
        fonte = session.query(FonteImagem).filter(
            FonteImagem.nome == nome).one()
        try:
            proximocarregamento = datetime.strptime(data, '%Y-%m-%d')
        except ValueError:
            print('Formato de data inválido. Formato correto AAAA-MM-DD.')
            return
        print(f'Criando agendamento de cópia de arquivos da Fonte de Imagens '
              f'{nome} a partir de {data} com a máscara {mascara}')
        if fonte.agendamento:
            agendamento = fonte.agendamento
            agendamento.mascarafiltro = mascara
            agendamento.proximocarregamento = proximocarregamento
        else:
            agendamento = Agendamento(mascara, fonte, proximocarregamento)
        session.add(agendamento)
        try:
            session.commit()
            print(f'Gravado: {agendamento}')
        except IntegrityError as err:
            session.rollback()
            print(f'ERRRO! Provável chave duplicada \n{err}')
    except NoResultFound as err:
        print(f'Fonte "{nome}" não encontrada')


@cli.command()
@click.pass_obj
def agendamento(ctx):
    """Processa um agendamento de cópia das fontes de imagem cadastradas."""
    trata_agendamentos(session)
    print('Fim do comando agendamento.')


@cli.command()
@click.pass_obj
@click.option('--lote', prompt=True, default=1000,
              help='Qtde de arquivos em cada BSON gerado')
def exporta(ctx, lote):
    """Processa um lote de imagens, exportando para BSON."""
    _, name, qtde = exporta_bson(session=session, batch_size=lote)
    print(f'{qtde} arquivos exportados para {name}')


@cli.command()
@click.pass_obj
@click.option('--intervalo', prompt=True, default=30,
              help='Intervalo em minutos entre execuções')
@click.option('--lote', prompt=True, default=1000,
              help='Qtde de arquivos em cada BSON gerado')
def daemon(ctx, intervalo, lote):
    """Deixa sistema rodando e processado cópias e exportações."""
    print('Entrando em modo "daemon". Pressione Ctrl+C para encerrar.')
    proximo = 0  # Loop inicial
    while True:
        atual = time.time()
        if proximo < atual:  # Chegou a hora de rodar novamente
            trata_agendamentos(session)
            exporta_bson(session, lote)
            proximo = time.time() + intervalo * 60
        time.sleep(1)


@cli.command()
@click.pass_obj
def stats(ctx):
    """Estatísticas do Banco de Dados ativo."""
    fontes = session.query(FonteImagem).all()
    for fonte in fontes:
        print(fonte.nome)
        print(fonte.caminho)
        print(f'Contêineres carregados no BD:'
              f'{fonte.total_imagens(session)}')
        print(f'Próximo agendamento: {fonte.proximo_agendamento(session)}')


if __name__ == '__main__':
    cli()
