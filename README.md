# mail-ai-agent

A Python agent that fetches unread emails via a mail proxy, analyses them using a local
LLM (Ollama), and automatically performs actions (move, delete, mark as read).

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- Mail proxy running at `http://127.0.0.1:8080`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
proxy:
  base_url: "http://127.0.0.1:8080"
  api_key: "your-api-key"

llm:
  model: "llama3.2"          # any Ollama model
  base_url: "http://127.0.0.1:11434"

agent:
  poll_interval: 300         # seconds between polling runs (watch mode)
  folder: null               # null = INBOX; or e.g. "INBOX.Pending"
  instructions: |
    - If the email is from a lead generation agency -> delete
    - If the email contains an invoice -> move to folder INBOX.Invoices
    - All other emails -> mark as read
```

> **Note:** `config.yaml` is listed in `.gitignore` and will never be committed
> (it contains the API key).

## Running

### One-shot (process all unread emails, then exit)

```bash
python -m mail_agent.main run
```

### Polling loop (runs until Ctrl+C)

```bash
python -m mail_agent.main watch
# or with a custom interval:
python -m mail_agent.main watch --interval 60
```

### Debug logging

```bash
python -m mail_agent.main -v run
```

All options:

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
# or with verbose output:
pytest -v
```

The tests mock both the HTTP client (no running mail proxy required) and
Ollama (no running LLM required).

## Project Structure

```
mail-ai-agent/
├── config.example.yaml      # template for config.yaml
├── requirements.txt
├── mail_agent/
│   ├── main.py              # CLI entry point (click)
│   ├── config.py            # config loading from YAML
│   ├── models.py            # Pydantic models (API schemas)
│   ├── proxy_client.py      # HTTP client for the mail proxy
│   ├── llm.py               # Ollama interface + prompt logic
│   └── agent.py             # core loop: fetch → analyse → act
└── tests/
    ├── test_proxy_client.py
    ├── test_llm.py
    └── test_agent.py
```

## Supported Actions

| Action | Description |
|---|---|
| `mark_read` | Mark email as read |
| `move` | Move email to another folder |
| `delete` | Delete email (goes to the proxy's trash) |
| `reply` | Not yet implemented — falls back to `mark_read` |

## LLM Prompt Language

The system prompt and JSON schema are written in English, as common open-source models
(llama3.2, mistral) produce the most reliable structured responses in that language.
The `instructions` in the config can be in German or English — the model understands both.
