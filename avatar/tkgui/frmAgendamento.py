import tkinter as tk

from datetime import datetime
from tkinter import messagebox

from avatar.models.models import Agendamento


class AgendamentoForm():

    def __init__(self, main, fonte):
        print(fonte)
        self.main = main
        self.session = main.session
        self.fonte = fonte
        self.top = tk.Toplevel()
        self.cria_form()
        self.agendamento = None

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
        tk.Button(self.top, text='Salvar', command=self.save).grid(
            row=3, column=1, sticky=tk.W, pady=4)
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
            self.session.save(self.agendamento)
            self.session.commit()
            self.top.destroy()
            del self
        except Exception as err:
            messagebox.showerror('Erro!', str(err))
