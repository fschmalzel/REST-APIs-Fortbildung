## Installation

Folgendes muss installiert sein:
* Python 3.12 oder uv
* quarto
* LaTeX (LuaTeX und extra fonts)

## Unterlagen

Mit quarto wird die Webseite und die .pdfs generiert.
```shell
cd quarto && quarto render
```

Alle Unterlagen sind dann in quarto/_site

## MessageBoard starten

Pakete installieren
```shell
pip install .
# oder
uv sync
```


Den Host und den Port muss man entsprechend anpassen.
RESET_PASSWORD ist für das zurücksetzen der Datenbank.
```shell
export PYTHONPATH=$(pwd)/python/src
export RESET_PASSWORD=abc123


uvicorn messageboard.main:app --host 127.0.0.1 --port 8000
# oder mit uv
uv run uvicorn messageboard.main:app --host 127.0.0.1 --port 8000
```