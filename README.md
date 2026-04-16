# mail-ai-agent

Ein Python-Agent, der ungelesene Mails über einen Mail-Proxy abruft, per lokalem LLM
(Ollama) analysiert und automatisch Aktionen ausführt (verschieben, löschen, als gelesen
markieren).

## Voraussetzungen

- Python 3.11+
- [Ollama](https://ollama.com) läuft lokal (`ollama serve`)
- Mail-Proxy läuft auf `http://127.0.0.1:8080`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration

```bash
cp config.example.yaml config.yaml
```

`config.yaml` anpassen:

```yaml
proxy:
  base_url: "http://127.0.0.1:8080"
  api_key: "dein-api-key"

llm:
  model: "llama3.2"          # beliebiges Ollama-Modell
  base_url: "http://127.0.0.1:11434"

agent:
  poll_interval: 300         # Sekunden zwischen Polling-Runs (watch-Modus)
  folder: null               # null = INBOX; oder z.B. "INBOX.Pending"
  instructions: |
    - Wenn die Mail von einer Lead-Generierungsagentur stammt -> löschen
    - Wenn die Mail eine Rechnung enthält -> in den Ordner INBOX.Invoices verschieben
    - Alle anderen Mails -> als gelesen markieren
```

> **Hinweis:** `config.yaml` ist in `.gitignore` eingetragen und wird nie committet
> (enthält den API-Key).

## Ausführen

### Einmalig (alle ungelesenen Mails verarbeiten, dann beenden)

```bash
python -m mail_agent.main run
```

### Polling-Loop (läuft bis Ctrl+C)

```bash
python -m mail_agent.main watch
# oder mit eigenem Interval:
python -m mail_agent.main watch --interval 60
```

### Debug-Logging

```bash
python -m mail_agent.main -v run
```

Alle Optionen:

```
Usage: python -m mail_agent.main [OPTIONS] COMMAND [ARGS]...

  Mail AI Agent — triage your inbox with a local LLM.

Options:
  --config TEXT  Path to the YAML config file.  [default: config.yaml]
  -v, --verbose  Enable debug logging.

Commands:
  run    Process all unread emails once, then exit.
  watch  Poll for new emails in a continuous loop. Stop with Ctrl+C.
```

## Unit Tests

```bash
pytest
# oder mit ausführlicher Ausgabe:
pytest -v
```

Die Tests mocken sowohl den HTTP-Client (kein laufender Mail-Proxy nötig) als auch
Ollama (kein laufendes LLM nötig).

## Projektstruktur

```
mail-ai-agent/
├── config.example.yaml      # Vorlage für config.yaml
├── requirements.txt
├── mail_agent/
│   ├── main.py              # CLI-Einstiegspunkt (click)
│   ├── config.py            # Config-Loading aus YAML
│   ├── models.py            # Pydantic-Modelle (API-Schemas)
│   ├── proxy_client.py      # HTTP-Client für den Mail-Proxy
│   ├── llm.py               # Ollama-Interface + Prompt-Logik
│   └── agent.py             # Kern-Loop: fetch → analyse → act
└── tests/
    ├── test_proxy_client.py
    ├── test_llm.py
    └── test_agent.py
```

## Unterstützte Aktionen

| Aktion | Beschreibung |
|---|---|
| `mark_read` | Mail als gelesen markieren |
| `move` | Mail in einen anderen Ordner verschieben |
| `delete` | Mail löschen (landet im Trash des Proxy) |
| `reply` | Noch nicht implementiert — fällt auf `mark_read` zurück |

## LLM-Prompt-Sprache

Der System-Prompt und das JSON-Schema sind auf Englisch formuliert, da gängige
Open-Source-Modelle (llama3.2, mistral) darin am zuverlässigsten strukturierte Antworten
liefern. Die `instructions` in der Config können auf Deutsch oder Englisch sein — das
Modell versteht beides.
