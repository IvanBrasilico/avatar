import tkinter as tk
from tkinter import messagebox

from avatar.models.models import FonteImagem
from avatar.tkgui.frmAgendamento import AgendamentoForm


class FonteForm():

    def __init__(self, main, fonte):
        self.main = main
        self.session = main.session
        self.fonte = fonte
        self.top = tk.Toplevel()
        self.cria_form()

    def cria_form(self):
        self.top.title("Fonte de Imagens")
        tk.Label(self.top, text="Nome").grid(row=0)
        tk.Label(self.top, text="Caminho").grid(row=1)
        self.edtNome = tk.Entry(self.top)
        self.edtCaminho = tk.Entry(self.top)
        self.edtNome.grid(row=0, column=1)
        self.edtCaminho.grid(row=1, column=1)
        tk.Button(self.top, text='Fechar', command=self.top.destroy).grid(
            row=3, column=0, sticky=tk.W, pady=4)
        tk.Button(self.top, text='Salvar', command=self.save).grid(
            row=3, column=1, sticky=tk.W, pady=4)
        tk.Button(self.top, text='Agendar', command=self.agendamento).grid(
            row=3, column=2, sticky=tk.W, pady=4)
        if self.fonte:
            self.edtNome.insert(10, self.fonte.nome)
            self.edtCaminho.insert(10, self.fonte.caminho)

    def save(self):
        try:
            fonte, msg = FonteImagem.cria_ou_edita(self.session,
                                      self.edtNome.get(),
                                      self.edtCaminho.get())
            self.main.update_fontes()
            messagebox.showinfo('FonteImagem', msg)
            self.top.destroy()
            del self
        except Exception as err:
            messagebox.showerror('Erro!', str(err))


    def agendamento(self):
        try:
            fonte, msg = FonteImagem.cria_ou_edita(self.session,
                                      self.edtNome.get(),
                                      self.edtCaminho.get())
            self.main.update_fontes()
            AgendamentoForm(self, fonte)
        except Exception as err:
            messagebox.showerror('Erro!', str(err))
