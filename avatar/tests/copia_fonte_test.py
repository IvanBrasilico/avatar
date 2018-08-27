# COMO Usuário Local do AVATAR,
# PRECISO cadastrar uma fonte de dados.
# PARA permitir a cópia periódica dos arquivos de imagens

import unittest
from avatar.models.models import Agendamento, Base, \
    ConteinerEscaneado, FonteImagem, MySession


class ModelTest(unittest.TestCase):

    def setUp(self):
        mysession = MySession(arquivo=None)
        self.session = mysession.session
        self.engine = mysession.engine

    def tearDown(self):
        pass

    def test_fonte_imagem(self):
        fonte = FonteImagem('Fonte 1', 'F1')
        self.session.add(fonte)
        self.session.commit()
        del fonte
        fonte = self.session.query(FonteImagem).filter(
            FonteImagem.nome == 'Fonte 1').one()
        assert fonte.caminho == 'F1'

    def test_conteinerescaneado(self):
        self.test_fonte_imagem()
        fonte = self.session.query(FonteImagem).filter(
            FonteImagem.nome == 'Fonte 1').one()
        conteiner = ConteinerEscaneado('C1', fonte)
        self.session.add(conteiner)
        self.session.commit()
        del conteiner
        conteiner = self.session.query(ConteinerEscaneado).filter(
            ConteinerEscaneado.numero == 'C1').one()
        assert conteiner.numero == 'C1'
        assert conteiner.fonte.id == fonte.id

    def test_agendamento(self):
        self.test_fonte_imagem()
        fonte = self.session.query(FonteImagem).filter(
            FonteImagem.nome == 'Fonte 1').one()
        agendamento = Agendamento('%Y', fonte)
        self.session.add(agendamento)
        self.session.commit()
        del agendamento
        agendamento = self.session.query(Agendamento).filter(
            Agendamento.mascarafiltro == '%Y').one()
        assert agendamento.mascarafiltro == '%Y'
        assert agendamento.fonte.id == fonte.id


class CopiaFonteTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_copia(self):
        pass


if __name__ == '__main__':
    unittest.main()
