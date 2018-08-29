"""Classe para testar funções de cópia.

COMO Usuário Local do AVATAR,
PRECISO ativar a cópia de imagens de uma FonteImagem.

Há uma estrutura de diretórios e arquivos para testes em tests/images:

A - diretório vazio caminho 208/08/29 (testar mensagem de diretório vazio)
B - XML mal formatado caminho 208/08/29 (testar mensagem de XML mal formatado)
C - XML OK, sem JPG caminho 208/08/29 (testar mensagem de Imagem n encontrada)
D - XML OK um JPG caminho 208/08/29 (testar se copiou JPEG e XML)
E - 2X XML OK um JPG caminhos 208/08/29 (testar se copiou 2 cjtos JPEG e XML)
"""
import datetime
import os
import unittest

from avatar.tests.base_models_test import BaseModelTest
from avatar.models.models import (Agendamento, FonteImagem)
from avatar.utils.utils import carregaarquivos


class CopiaTest(BaseModelTest):

    def test_A(self):
        fonte = FonteImagem('A', r'avatar\tests\images\A')
        agendamento = Agendamento('%Y\%m\%d', fonte)
        agendamento.proximocarregamento = datetime.datetime(2018, 8, 29)
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, self.session)
        assert erro is True
        assert "vazia" in mensagem

    def test_B(self):
        fonte = FonteImagem('B', r'avatar\tests\images\B')
        agendamento = Agendamento('%Y\%m\%d', fonte)
        agendamento.proximocarregamento = datetime.datetime(2018, 8, 29)
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, self.session)
        assert erro is True
        assert "vazia" in mensagem

    def test_C(self):
        fonte = FonteImagem('C', r'avatar\tests\images\C')
        agendamento = Agendamento('%Y\%m\%d', fonte)
        agendamento.proximocarregamento = datetime.datetime(2018, 8, 29)
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, self.session)
        assert erro is True
        assert "vazia" in mensagem

    def test_D(self):
        fonte = FonteImagem('D', r'avatar\tests\images\D')
        agendamento = Agendamento('%Y\%m\%d', fonte)
        agendamento.proximocarregamento = datetime.datetime(2018, 8, 29)
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, self.session)
        try:
            os.rmdir('images')
        except FileNotFoundError:
            pass
        assert erro is True
        print(os.getcwd())
        assert "TESET" in mensagem

    def test_E(self):
        fonte = FonteImagem('E', r'avatar\tests\images\E')
        agendamento = Agendamento('%Y\%m\%d', fonte)
        agendamento.proximocarregamento = datetime.datetime(2018, 8, 29)
        mensagem, erro = carregaarquivos(agendamento.processamascara(),
                                         fonte, self.session)
        try:
            os.rmdir('images')
        except FileNotFoundError:
            pass
        assert erro is True
        assert "vazia" in mensagem


if __name__ == '__main__':
    unittest.main()
