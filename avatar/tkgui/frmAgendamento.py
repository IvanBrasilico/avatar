import tkinter as tk

from datetime import datetime
from tkinter import messagebox

from avatar.models.models import Agendamento
from avatar.utils.utils import trata_agendamentos
from avatar.utils.dir_utils import detecta_mascara

class AgendamentoForm():

    def __init__(self, main, fonte):
        print(fonte)
        self.agendamento = None
        self.main = main
        self.session = main.session
        self.fonte = fonte
        self.top = tk.Toplevel()
        self.cria_form()

    def cria_form(self):
        self.top.title('Agendamento')
        tk.Label(self.top, text='Próximo agendamento').grid(row=0)
        tk.Label(self.top, text='Máscara').grid(row=1)
        tk.Label(self.top, text='Dias para repetir').grid(row=1)
        self.edtProximo = tk.Entry(self.top)
        self.edtMascara = tk.Entry(self.top)
        self.edtDias = tk.Entry(self.top)
        self.edtProximo.grid(row=0, column=1)
        self.edtMascara.grid(row=1, column=1)
        self.edtDias.grid(row=2, column=1)
        tk.Button(self.top, text='Fechar', command=self.top.destroy).grid(
            row=3, column=0, sticky=tk.W, pady=4)
        tk.Button(self.top, text='Salvar', command=self.save_and_close).grid(
            row=3, column=1, sticky=tk.W, pady=4)
        tk.Button(self.top, text='Detectar', command=self.detect).grid(
            row=3, column=2, sticky=tk.W, pady=4)
        tk.Button(self.top, text='Rodar', command=self.run).grid(
            row=3, column=3, sticky=tk.W, pady=4)
        if self.fonte.agendamento:
            agendamento = self.fonte.agendamento
            self.edtProximo.insert(10, agendamento.get_proximocarregamento_fmt())
            self.edtMascara.insert(10, agendamento.mascarafiltro)
            self.edtDias.insert(10, agendamento.diaspararepetir)
            self.agendamento = agendamento
        else:
            self.edtProximo.insert(10,
                                   datetime.now().strftime('%Y-%m-%d %H:%M'))
            self.edtMascara.insert(10, '%Y\%m\%d')
            self.edtDias.insert(10, 1)

    def save(self):
        try:
            if not self.agendamento:
                self.agendamento = Agendamento(self.edtMascara.get(),
                                               self.fonte,
                                               datetime.now())
            self.agendamento.set_proximocarregamento(self.edtProximo.get())
            try:
                self.agendamento.diaspararepetir = int(self.edtDias.get())
            except ValueError:
                raise ValueError(self.edtDias.get() +
                                 'não é um número válido.')
            self.agendamento.mascarafiltro = self.edtMascara.get()
            self.session.add(self.agendamento)
            self.session.commit()
            return True
        except Exception as err:
            messagebox.showerror('Erro!', str(err))
            return False


    def save_and_close(self):
        if self.save():
            self.top.destroy()
            del self

    def state_ok(self):
        state_ok = True
        if not self.agendamento:
            state_ok = self.save()
        return state_ok

    def run(self):
        if self.state_ok() is True:
            mensagem, erro = trata_agendamentos(self.session, self.agendamento)
            if erro:
                messagebox.showerror('Trata agendamentos', mensagem)
            else:
                messagebox.showinfo('Trata agendamentos', mensagem)

    def detecta(self):
        self.edtMascara = detecta_mascara(self.fonte.caminho)