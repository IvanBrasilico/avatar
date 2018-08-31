import tkinter as tk

from avatar.models.models import FonteImagem
from tkinter import messagebox


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
        if self.fonte:
            self.edtNome.insert(10, self.fonte.nome)
            self.edtCaminho.insert(10, self.fonte.caminho)

    def save(self):
        try:
            FonteImagem.cria_ou_edita(self.session,
                                      self.edtNome.get(),
                                      self.edtCaminho.get())
            self.main.update_fontes()
            self.top.destroy()
            del self
        except Exception as err:
            messagebox.showerror('Erro!', str(err))


def frm_fonte(fonte):
    this = tk.Toplevel()
    this.title("Fonte de Imagens")
    tk.Label(this, text="Nome").grid(row=0)
    tk.Label(this, text="Caminho").grid(row=1)
    e1 = tk.Entry(this)
    e2 = tk.Entry(this)
    e1.grid(row=0, column=1)
    e2.grid(row=1, column=1)
    tk.Button(this, text='Cancelar', command=this.destroy).grid(row=3, column=0, sticky=W, pady=4)
    tk.Button(this, text='Salvar').grid(row=3, column=1, sticky=W, pady=4)
    if fonte:
        e1.insert(10, fonte.nome)
        e2.insert(10, fonte.caminho)
