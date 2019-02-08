"""Classe para testar funções de cópia.

COMO Usuário Local do AVATAR,
PRECISO ativar a cópia de imagens de uma FonteImagem.

Há uma estrutura de diretórios e arquivos para testes em tests/images:

A - diretório vazio caminho 208/08/29 (testar mensagem de diretório vazio)
B - XML mal formatado caminho 208/08/29 (testar mensagem de XML mal formatado)
C - XML OK, sem JPG caminho 208/08/29 (testar mensagem de Imagem n encontrada)
D - XML OK um JPG caminho 208/08/29 (testar se copiou JPEG e XML)
E - 2X XML OK um JPG caminhos 208/08/29 (testar se copiou 2 cjtos JPEG e XML)
F - XML faltando campos caminho 208/08/29 (testar mensagem XML mal formatado)

"""
import datetime
import os
import shutil
import unittest

from avatar.tests.base_models_test import BaseModelTest
from avatar.models.models import (Agendamento, FonteImagem)
from avatar.utils.utils import (carregaarquivos, exporta_bson,
                                trata_agendamentos)

DATA = datetime.datetime(2018, 8, 29)
CAMINHO = r'avatar\tests\images'
JPEG_DESTINO = 'avatar/tests/images/D/2018/08/29/MSKU01/msku01fake_stamp.jpg'


class CopiaTest(BaseModelTest):

    def cria_fonte_agendamento(self, nome: str):
        fonte = FonteImagem(nome, os.path.join(CAMINHO, nome))
        agendamento = Agendamento('%Y\%m\%d', fonte, DATA)
        self.session.add(fonte)
        self.session.add(agendamento)
        self.session.commit()
        return agendamento

    def test_A(self):
        agendamento = self.cria_fonte_agendamento('A')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        assert erro is True
        assert 'retornou lista vazia' in mensagem

    def test_B(self):
        agendamento = self.cria_fonte_agendamento('B')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        assert erro is True
        assert 'XML inválido' in mensagem

    def test_C(self):
        agendamento = self.cria_fonte_agendamento('C')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        assert erro is True
        assert 'Imagem não encontrada' in mensagem

    def test_D(self):
        agendamento = self.cria_fonte_agendamento('D')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        try:
            assert os.path.exists(JPEG_DESTINO)
            shutil.rmtree('images/D')
        except FileNotFoundError:
            assert False
        assert mensagem == ''
        assert erro is False

    def test_E(self):
        agendamento = self.cria_fonte_agendamento('E')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        try:
            shutil.rmtree('images/E')
        except FileNotFoundError:
            assert False
        assert mensagem == ''
        assert erro is False

    def test_F(self):
        agendamento = self.cria_fonte_agendamento('F')
        mensagem, erro = carregaarquivos(agendamento, self.session)
        assert 'XML inválido' in mensagem

    def test_agendamento_bson(self):
        self.cria_fonte_agendamento('D')
        trata_agendamentos(self.session)
        exportados, name, qtde = exporta_bson(self.session, 1)
        try:
            assert os.path.exists(JPEG_DESTINO)
            shutil.rmtree('images/D')
            print(exportados, name, qtde)
            assert os.path.exists(name)
            os.remove(name)
        except FileNotFoundError:
            assert False


if __name__ == '__main__':
    unittest.main()
