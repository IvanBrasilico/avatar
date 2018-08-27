"""Script de linha de comando para integração do arquivo XML.
Script de linha de comando para fazer atualização 'manual'
dos metadados do arquivo XML nas imagens.
Args:
    year: ano de início da pesquisa
    month: mês de início da pesquisa
    batch_size: tamanho do lote de atualização/limite de registros da consulta
"""
import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from avatar.cli import session
from avatar.models.models import FonteImagem


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.obj = debug


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.option('--caminho', prompt=True,
              help='Caminho Local para acesso'
                   'às imagens (Unidade de disco e pasta)')
@click.pass_obj
def add(ctx, nome, caminho):
    """Adiciona fonte de imagem.
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
    print(session.query(FonteImagem).filter(FonteImagem.nome == nome).delete())
    session.commit()
    print(f'FonteImagem {nome} excluída')


@cli.command()
@click.option('--nome', prompt=True, help='Nome da fonte de imagens (Recinto)')
@click.option('--data', prompt=True, help='Data a copiar')
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
        print(f'Iniciando cópia de arquivos da Fonte de Imagens {nome}'
              f' a partir de {data}')
        
    except NoResultFound as err:
        print(f'Fonte "{nome}" não encontrada')


if __name__ == '__main__':
    cli()
