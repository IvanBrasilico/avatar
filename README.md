# avatar
Versão 2.0 do módulo "externo" do sistema AJNA. Módulo faz a "captura" de imagens e encapsulamento em lotes BSON.


Instalação desenvolvedor

```
$ git clone http://github.com/avatar.git
$ pip install -e .[dev]
```

Criação de executável

```
> pyinstaller --onefile avatar/tkgui/avatar_gui.py

> pyinstaller --onefile avatar/cli/avatar_cli.py

> pyinstaller --onefile avatar/cli/avatar_upload_bson.py
```



