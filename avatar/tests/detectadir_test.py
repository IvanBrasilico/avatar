"""Classe para testar funções de detecção automática de caminho.

COMO Usuário Local do AVATAR,
QUERO descobrir máscara dos diretórios das fontes de dados.

Há uma estrutura de diretórios e arquivos para testes em tests/fonts:

A - diretório caminho %Y/%m/%d
B - diretório caminho %Y%m/%Y%m%d
A - diretório caminho %Y/#%m/#%d
"""
import os
import unittest
import sys

from avatar.utils.dir_utils import pega_letras, detecta_mascara

CAMINHO = os.path.join('avatar', 'tests', 'fonts')


class CopiaTest(unittest.TestCase):

    def test_pegaletras(self):
        letras = pega_letras()
        if sys.platform == 'win32':
            assert letras == ['C:', 'D:']

    def test_A(self):
        mascara = detecta_mascara(os.path.join(CAMINHO, 'A'))
        print(mascara)
        assert mascara == '%Y/%m/%d'

    def test_B(self):
        mascara = detecta_mascara(os.path.join(CAMINHO, 'B'))
        print(mascara)
        assert mascara == '%Y%m/%Y%m%d'

    def test_C(self):
        mascara = detecta_mascara(os.path.join(CAMINHO, 'C'))
        print(mascara)
        assert mascara == '%Y/#%m/#%d'


if __name__ == '__main__':
    unittest.main()
