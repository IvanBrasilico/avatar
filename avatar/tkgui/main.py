"""Interface gráfica para uso do Avatar."""
import time
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from avatar.models.models import Agendamento, FonteImagem, MySession
from avatar.utils.utils import (carregaarquivos, exporta_bson,
                                trata_agendamentos)
from avatar.utils.logconf import console, logger
from logging import DEBUG
import tkinter as tk
from tkinter import messagebox


class Application(tk.Frame):
    def __init__(self, session, master=None):
        super().__init__(master)
        self.session = session
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.listbox = tk.Listbox(self)
        self.listbox.pack(side='left')
        fontes = self.session.query(FonteImagem).all()
        for fonte in fontes:
            self.listbox.insert(tk.END, fonte.nome)

        self.btnNovaFonte = tk.Button(self)
        self.btnNovaFonte['text'] = 'Nova Fonte de Imagem'
        self.btnNovaFonte['command'] = self.edita_fonte(True)
        self.btnNovaFonte.pack(side='top')
        self.btnEditaFonte = tk.Button(self)
        self.btnEditaFonte['text'] = 'Editar Fonte de Imagem'
        self.btnEditaFonte['command'] = self.edita_fonte(False)
        self.btnEditaFonte.pack(side='top')
        self.btnAgendamento = tk.Button(self)
        self.btnAgendamento['text'] = 'Trata agendamentos'
        self.btnAgendamento['command'] = self.trata_agendamento
        self.btnAgendamento.pack(side='top')
        self.btnExportaBSON = tk.Button(self)
        self.btnExportaBSON['text'] = 'Exporta BSON'
        self.btnExportaBSON['command'] = self.exporta_bson
        self.btnExportaBSON.pack(side='top')
        self.btnQuit = tk.Button(self, text='QUIT', fg='red',
                              command=root.destroy)
        self.btnQuit.pack(side='bottom')

    def trata_agendamento(self):
        mensagem, erro = trata_agendamentos(self.session)
        if erro:
            messagebox.showerror('Trata agendamentos', mensagem)
        else:
            messagebox.showinfo('Trata agendamentos', mensagem)

    def exporta_bson(self, lote=1000):
        _, name, qtde = exporta_bson(session=self.session, batch_size=lote)
        messagebox.showinfo('Exporta BSON',
                            f'{qtde} arquivos exportados. {name}')

    def edita_fonte(self, nova: bool=True):
        if nova:
            fonte = FonteImagem()
        else:
            pass
        # Open Window
mysession = MySession()
root = tk.Tk()
app = Application(mysession.session, master=root)
app.mainloop()
