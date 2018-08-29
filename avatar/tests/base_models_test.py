"""Classe base que conecta BD."""
import unittest

from avatar.models.models import (Base, MySession)


class BaseModelTest(unittest.TestCase):

    def setUp(self):
        mysession = MySession(arquivo=None)
        self.session = mysession.session
        self.engine = mysession.engine

    def tearDown(self):
        pass
