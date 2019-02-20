import os
import win32api
from datetime import datetime

ANO = str(datetime.now().year)


def pega_fontes():
    fontes = []
    for drive in pega_letras():
        for dir in os.listdir(drive):
            if os.path.isdir(os.path.join(drive, dir)):
                try:
                    caminho = os.path.join(drive, dir)
                    if not detecta_mascara(caminho) == []:
                        fontes.add(caminho)
                except ValueError:
                    continue
    return fontes

def pega_letras():
    drives = win32api.GetLogicalDriveStrings()
    drives = [drive[:2] for drive in drives.split('\000')[:-1]]
    return drives


def formata_mascaras(pastas: list) -> str:
    mascaras = []
    for nivel, pasta in enumerate(pastas):
        mascaras.append(mask_of_data(pasta, nivel))
    return '/'.join(mascaras)


def mask_of_data(pasta: str, nivel: int = 0) -> bool:
    masks = ('%Y', '%m', '%d')
    compose_masks = ('%Y%m%d', '%Y%m', '%m%d')
    for try_mask in masks[nivel:]:
        try:
            prefix = ''
            if len(pasta) == 1:
                pasta = '0' + pasta
                prefix = '#'
            datetime.strptime(pasta, try_mask)
            return prefix + try_mask
        except ValueError:
            continue
    for try_mask in compose_masks:
        try:
            datetime.strptime(pasta, try_mask)
            return try_mask
        except ValueError:
            continue
    return None


def detecta(caminho: str, pastas: list):
    lista_pastas = os.listdir(os.path.join(caminho, *pastas))
    if len(lista_pastas) == 0:
        return formata_mascaras(pastas)
    if len(pastas) == 0:
        lpastas = [pasta for pasta in lista_pastas if pasta[:4] == ANO]
        if len(lpastas) == 0:
            return pastas
    pasta = lista_pastas[0]
    if mask_of_data(pasta) is not None:
        pastas.append(pasta)
        return detecta(caminho, pastas)
    if len(pastas) > 0: # Achou o pote no fim do arco-íris
        return formata_mascaras(pastas)
    raise ValueError('Caminho %s inválido para a função detecta_mascara!!!'
                     % caminho)


def detecta_mascara(caminho: str):
    mascaras = []
    return detecta(caminho, mascaras)
