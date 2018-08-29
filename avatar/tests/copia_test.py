"""Classe para testar funções de cópia.

COMO Usuário Local do AVATAR,
PRECISO ativar a cópia de imagens de uma FonteImagem.

Testes:

A - diretório vazio caminho 208/08/29 (testar mensagem de diretório vazio)
B - XML mal formatado caminho 208/08/29 (testar mensagem de XML mal formatado)
C - XML OK, sem JPG caminho 208/08/29 (testar mensagem de Imagem não encontrada)
D - XML OK um JPG caminho 208/08/29 (testar se copiou JPEG e XML)
E - 2X XML OK um JPG caminhos 208/08/29 (testar se copiou 2 conjuntos JPEG e XML)
"""

import unittest
from avatar.tests.base_models_test import BaseModelTest
from avatar.models.models import (Agendamento, Base, ConteinerEscaneado,
                                  FonteImagem, MySession)

class CopiaFonteTest(BaseModelTest):

    def setUp(self):
        super().setUp()

    def test_A(self):
        pass


if __name__ == '__main__':
    unittest.main()
