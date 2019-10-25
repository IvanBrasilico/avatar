"""Interface gráfica para UPLOAD de images e bsons."""
import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, '.')
print(sys.path)

from avatar.utils.conf import BSON_DIR, VIRASANA_URL
from avatar.utils.dir_monitor import despacha_dir

IMAGES_DIR = ''


class Application():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Auxiliar de Uploads do AJNA')
        self.create_widgets()

    def create_widgets(self):
        # Create some room around all the internal frames
        self.window['padx'] = 5
        self.window['pady'] = 5
        # - - - - - - - - - - - - - - - - - - - - -
        # Frame BSON
        frame1 = ttk.Frame(self.window, relief=tk.RIDGE)
        frame1.grid(row=8, column=3, sticky=tk.W,
                    padx=10, pady=10, ipadx=10, ipady=10)
        self.lblSpace = tk.Label(frame1)
        self.lblSpace.grid(row=1, column=2)
        self.lblBsondir = tk.Label(frame1, text='BSON dir')
        self.edtBsondir = tk.Entry(frame1)
        self.edtBsondir.insert(0, BSON_DIR)
        self.lblBsondir.grid(row=2, column=1, sticky=tk.W)
        self.edtBsondir.grid(row=2, column=2, sticky=tk.W)
        self.lblUrl = tk.Label(frame1, text='URL do virasana')
        self.edtUrl = tk.Entry(frame1, width=40)
        self.edtUrl.insert(0, VIRASANA_URL)
        self.lblUrl.grid(row=3, column=1, sticky=tk.W)
        self.edtUrl.grid(row=3, column=2, sticky=tk.W)
        self.btnUploadBson = tk.Button(frame1)
        self.btnUploadBson['text'] = 'UPLOAD diretório bson'
        self.btnUploadBson.grid(row=3, column=3)
        self.btnUploadBson['command'] = self.upload_bsons
        self.lblSpace = tk.Label(frame1)
        self.lblSpace.grid(row=4, column=2)
        self.lblImagesdir = tk.Label(frame1, text='Images dir')
        self.edtImagesdir = tk.Entry(frame1)
        self.edtImagesdir.insert(0, IMAGES_DIR)
        self.lblImagesdir.grid(row=5, column=1, sticky=tk.W)
        self.edtImagesdir.grid(row=5, column=2, sticky=tk.W)
        self.lblTag = tk.Label(frame1, text='Tag a incluir')
        self.edtTag = tk.Entry(frame1)
        self.edtTag.insert(0, 'drogas')
        self.lblTag.grid(row=5, column=1, sticky=tk.W)
        self.edtTag.grid(row=5, column=2, sticky=tk.W)
        self.btnUploadImages = tk.Button(frame1)
        self.btnUploadImages['text'] = 'UPLOAD diretório de imagens'
        self.btnUploadImages.grid(row=5, column=3)
        self.btnUploadImages['command'] = self.upload_imagens
        self.lblSpace = tk.Label(frame1)
        self.lblSpace.grid(row=7, column=2)

        # Quit button in the lower right corner
        quit_button = ttk.Button(frame1, text="Quit", command=self.window.destroy)
        quit_button.grid(row=8, column=1)

    def upload_bsons(self):
        print('Iniciando upload...')
        dir = self.edtBsondir.get()
        url = self.edtUrl.get()
        print(despacha_dir(dir=dir, url=url, sync=True))

    def upload_imagens(self):
        dir = self.edtImagesdir.get()
        

if __name__ == '__main__':
    app = Application()
    app.window.mainloop()
