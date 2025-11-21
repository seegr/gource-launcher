# Gource Launcher

Interaktivní launcher pro [gource](https://gource.io/) s podporou Google Fonts a GitHub repozitářů.

## Požadavky

- Python 3.10+
- [gource](https://gource.io/) (`brew install gource`)
- [gh CLI](https://cli.github.com/) (pro GitHub repos)

## Instalace

```bash
poetry install
```

## Spuštění

```bash
poetry run python app.py
```

## Konfigurace

Vytvoř `.env` soubor:

```
GOOGLE_FONTS_API_KEY=tvuj_api_klic
```

API klíč získáš na [Google Fonts API](https://developers.google.com/fonts/docs/developer_api).
