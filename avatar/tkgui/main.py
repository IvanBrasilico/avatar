"""Interface gráfica para uso do Avatar."""
import time
import tkinter as tk
import os
import sys
from tkinter import messagebox
from threading import Thread

from avatar.models.models import Agendamento, FonteImagem, MySession
from avatar.tkgui.frmFonte import FonteForm
from avatar.utils.utils import (carregaarquivos, exporta_bson,
                                trata_agendamentos)
from avatar.utils.logconf import logger
from logging import DEBUG

LOTE = 1
INTERVALO = 30

class Application(tk.Frame):
    def __init__(self, session, master):
        super().__init__(master)
        self.session = session
        self.pack()
        self.create_widgets()
        master.protocol("WM_DELETE_WINDOW", self._close)

    def create_widgets(self):
        self.listbox = tk.Listbox(self)
        self.listbox.pack(side='left')
        self.update_fontes()

        BTN_WIDTH = 20
        self.btnNovaFonte = tk.Button(self, width=BTN_WIDTH)
        self.btnNovaFonte['text'] = 'Nova Fonte de Imagem'
        self.btnNovaFonte['command'] = self.janela_fonte
        self.btnNovaFonte.pack(side='top')
        self.btnEditaFonte = tk.Button(self, width=BTN_WIDTH)
        self.btnEditaFonte['text'] = 'Editar Fonte de Imagem'
        self.btnEditaFonte['command'] = self.edita_fonte
        self.btnEditaFonte.pack(side='top')
        self.btnExcluiFonte = tk.Button(self, width=BTN_WIDTH)
        self.btnExcluiFonte['text'] = 'Excluir Fonte de Imagem'
        self.btnExcluiFonte['command'] = self.exclui_fonte
        self.btnExcluiFonte.pack(side='top')
        self.btnAgendamento = tk.Button(self, width=BTN_WIDTH)
        self.btnAgendamento['text'] = 'Trata agendamentos'
        self.btnAgendamento['command'] = self.trata_agendamento
        self.btnAgendamento.pack(side='top')
        self.btnExportaBSON = tk.Button(self, width=BTN_WIDTH)
        self.btnExportaBSON['text'] = 'Exporta BSON'
        self.btnExportaBSON['command'] = self.exporta_bson
        self.btnExportaBSON.pack(side='top')
        self.btnAbrirLog = tk.Button(self, width=BTN_WIDTH)
        self.btnAbrirLog['text'] = 'Ver Log'
        self.btnAbrirLog['command'] = self.ver_log
        self.btnAbrirLog.pack(side='top')
        self.btnDaemon = tk.Button(self, width=BTN_WIDTH)
        self.btnDaemon['text'] = 'Iniciar Serviço'
        self.btnDaemon['command'] = self.daemon_toggle
        self.btnDaemon.pack(side='top')
        self.btnQuit = tk.Button(self, text='Sair',
                                 command=self._close,
                                 width=BTN_WIDTH)
        self.btnQuit.pack(side='bottom')
        self.daemon = None

    def update_fontes(self):
        self.listbox.delete(0, tk.END)
        fontes = self.session.query(FonteImagem).all()
        for fonte in fontes:
            self.listbox.insert(tk.END, fonte.nome)

    def get_fonte(self):
        select = self.listbox.curselection()
        if select:
            nome = self.listbox.get(select)
            return self.session.query(FonteImagem).filter(
                FonteImagem.nome == nome).first()
        else:
            messagebox.showinfo('Editar', "Selecione um item da lista")

    def edita_fonte(self):
        fonte = self.get_fonte()
        if fonte:
            self.janela_fonte(fonte)

    def janela_fonte(self, fonte=None):
        FonteForm(self, fonte)

    def exclui_fonte(self):
        fonte = self.get_fonte()
        if fonte:
            try:
                fonte.exclui(self.session)
                messagebox.showinfo('Excluir', "Fonte de Imagem Excluída.")
                self.update_fontes()
            except Exception as err:
                messagebox.showerror('Excluir', str(err))

    def trata_agendamento(self):
        mensagem, erro = trata_agendamentos(self.session)
        if erro:
            messagebox.showerror('Trata agendamentos', mensagem)
        else:
            messagebox.showinfo('Trata agendamentos', mensagem)

    def exporta_bson(self):
        _, name, qtde = exporta_bson(session=self.session, batch_size=1000)
        messagebox.showinfo('Exporta BSON',
                            f'{qtde} arquivos exportados. {name}')

    def ver_log(self):
        os.startfile('avatar.log')

    def daemon_toggle(self):
        if 'Iniciar' in self.btnDaemon['text']:
            self.daemon = Thread(target=self.daemon_function)
            self.daemon_signal = True
            self.daemon.start()
            self.btnDaemon['text'] = '* Encerrar Serviço'
        else:
            self.daemon_signal = False
            self.daemon.join(timeout=30)
            self.btnDaemon['text'] = 'Iniciar Serviço'

    def daemon_function(self):
        threadsession = MySession()
        proximo = 0  # Loop inicial
        while self.daemon_signal:
            atual = time.time()
            if proximo < atual:  # Chegou a hora de rodar novamente
                trata_agendamentos(threadsession.session)
                exporta_bson(threadsession.session, LOTE)
                proximo = time.time() + INTERVALO * 60
            time.sleep(1)

    def _close(self):
        print('Encerrando...')
        if 'Encerrar' in self.btnDaemon['text']:
            self.daemon_signal = False
            self.daemon.join(timeout=30)
        self.quit()

if '--debug' in sys.argv:
    print('Iniciando modo DEBUG')
    logger.setLevel(DEBUG)
mysession = MySession()
root = tk.Tk()
app = Application(mysession.session, master=root)
app.mainloop()
