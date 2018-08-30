"""Script de linha de comando para integração do arquivo XML.
Script de linha de comando para fazer atualização 'manual'
dos metadados do arquivo XML nas imagens.
Args:
    year: ano de início da pesquisa
    month: mês de início da pesquisa
    batch_size: tamanho do lote de atualização/limite de registros da consulta
"""
import click
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
    fonte = session.query(FonteImagem).filter(FonteImagem.nome == nome).first()
    if fonte is None:
        fonte = FonteImagem(nome, caminho)
    else:
        fonte.caminho = caminho
    session.add(fonte)
    try:
        session.commit()
        print(f'Gravado: {fonte}')
    except IntegrityError as err:
        session.rollback()
        print(f'ERRRO! Provável chave duplicada \n{err}')


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


@cli.command()
@click.pass_obj
@click.option('--lote', prompt=True, default=1000,
              help='Qtde de arquivos em cada BSON gerado')
def exporta(ctx, lote):
    """Processa um lote de imagens, exportando para BSON."""
    exporta_bson(session=session, batch_size=lote)


@cli.command()
@click.pass_obj
@click.option('--intervalo', prompt=True,
              help='Intervalo em minutos entre execuções')
@click.option('--lote', prompt=True,
              help='Qtde de arquivos em cada BSON gerado')
def daemon(ctx):
    """Deixa sistema rodando e processado cópias e exportações."""
    pass


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
